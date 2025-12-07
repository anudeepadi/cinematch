"""
Collaborative filtering recommender using user-item interaction patterns.
"""

from typing import List, Dict, Set
from collections import defaultdict
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.movie import Movie
from app.models.interaction import UserMovieInteraction, WatchHistory
from app.services.recommenders.base import (
    BaseRecommender,
    RecommendationResult,
    UserPreferences,
    RecommendationContext
)


class CollaborativeFilteringRecommender(BaseRecommender):
    """
    Collaborative filtering recommender using item-based similarity.

    Algorithm:
    1. Find users with similar taste (based on common liked movies)
    2. Find movies those similar users liked that current user hasn't seen
    3. Score by how many similar users liked each movie
    4. Weight by user similarity
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.min_similar_users = 3
        self.min_common_movies = 2

    @property
    def name(self) -> str:
        return "collaborative"

    def get_weight(self, history_count: int) -> float:
        # Collaborative filtering needs significant history
        if history_count < 5:
            return 0.05  # Very low weight with little history
        elif history_count < 10:
            return 0.15
        elif history_count < 20:
            return 0.25
        else:
            return 0.35  # Strong weight with lots of history

    async def recommend(
        self,
        user_preferences: UserPreferences,
        context: RecommendationContext,
        count: int = 10
    ) -> List[RecommendationResult]:
        """Generate collaborative filtering recommendations"""

        # Need minimum history for collaborative filtering
        if len(user_preferences.liked_movie_ids) < self.min_common_movies:
            return await self._popularity_fallback(context, count)

        # Find similar users
        similar_users = await self._find_similar_users(
            user_preferences.user_id,
            set(user_preferences.liked_movie_ids)
        )

        if len(similar_users) < self.min_similar_users:
            return await self._popularity_fallback(context, count)

        # Get movies liked by similar users
        candidate_movies = await self._get_candidates_from_similar_users(
            similar_users,
            user_preferences,
            context
        )

        if not candidate_movies:
            return await self._popularity_fallback(context, count)

        # Score candidates
        scored_candidates = self._score_candidates(
            candidate_movies,
            similar_users,
            user_preferences
        )

        # Take top N
        top_candidates = sorted(
            scored_candidates.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )[:count]

        # Fetch movie details and build results
        movie_ids = [movie_id for movie_id, _ in top_candidates]
        movies = await self._get_movies_by_ids(movie_ids)
        movie_map = {m.id: m for m in movies}

        results = []
        for movie_id, data in top_candidates:
            movie = movie_map.get(movie_id)
            if movie:
                reasoning = self._generate_reasoning(
                    movie, data["similar_user_count"], data["avg_rating"]
                )
                results.append(RecommendationResult(
                    movie_id=movie.id,
                    tmdb_id=movie.tmdb_id,
                    title=movie.title,
                    score=data["score"],
                    reasoning=reasoning,
                    source=self.name,
                    metadata={
                        "similar_users": data["similar_user_count"],
                        "avg_rating": data["avg_rating"]
                    }
                ))

        return results

    async def _find_similar_users(
        self,
        user_id: int,
        user_liked_movies: Set[int]
    ) -> Dict[int, float]:
        """Find users with similar taste based on common liked movies"""

        if not user_liked_movies:
            return {}

        # Get other users who liked the same movies
        result = await self.db.execute(
            select(
                UserMovieInteraction.user_id,
                UserMovieInteraction.movie_id
            ).where(
                UserMovieInteraction.movie_id.in_(user_liked_movies),
                UserMovieInteraction.user_id != user_id,
                UserMovieInteraction.interaction_type.in_(["watch", "favorite", "watched"])
            )
        )

        # Count common movies per user
        user_common_movies = defaultdict(set)
        for row in result.all():
            user_common_movies[row.user_id].add(row.movie_id)

        # Calculate similarity (Jaccard-like)
        similar_users = {}
        for other_user_id, common_movies in user_common_movies.items():
            if len(common_movies) >= self.min_common_movies:
                # Get total movies liked by other user
                other_result = await self.db.execute(
                    select(func.count(UserMovieInteraction.id)).where(
                        UserMovieInteraction.user_id == other_user_id,
                        UserMovieInteraction.interaction_type.in_(["watch", "favorite", "watched"])
                    )
                )
                other_total = other_result.scalar() or 0

                if other_total > 0:
                    # Jaccard similarity
                    union_size = len(user_liked_movies) + other_total - len(common_movies)
                    similarity = len(common_movies) / union_size if union_size > 0 else 0
                    similar_users[other_user_id] = similarity

        # Return top similar users
        sorted_users = sorted(similar_users.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_users[:50])  # Top 50 similar users

    async def _get_candidates_from_similar_users(
        self,
        similar_users: Dict[int, float],
        user_preferences: UserPreferences,
        context: RecommendationContext
    ) -> Dict[int, List[tuple]]:
        """Get movies liked by similar users that current user hasn't seen"""

        if not similar_users:
            return {}

        # Movies to exclude
        exclude_ids = set(context.exclude_movie_ids)
        exclude_ids.update(user_preferences.watched_movie_ids)
        exclude_ids.update(user_preferences.liked_movie_ids)
        exclude_ids.update(user_preferences.disliked_movie_ids)

        # Get interactions from similar users
        result = await self.db.execute(
            select(
                UserMovieInteraction.user_id,
                UserMovieInteraction.movie_id,
                UserMovieInteraction.rating
            ).where(
                UserMovieInteraction.user_id.in_(similar_users.keys()),
                UserMovieInteraction.interaction_type.in_(["watch", "favorite", "watched"]),
                UserMovieInteraction.movie_id.notin_(exclude_ids) if exclude_ids else True
            )
        )

        # Group by movie
        movie_interactions = defaultdict(list)
        for row in result.all():
            similarity = similar_users.get(row.user_id, 0)
            movie_interactions[row.movie_id].append((
                row.user_id,
                similarity,
                row.rating or 7.0  # Default rating if none
            ))

        return dict(movie_interactions)

    def _score_candidates(
        self,
        candidate_movies: Dict[int, List[tuple]],
        similar_users: Dict[int, float],
        user_preferences: UserPreferences
    ) -> Dict[int, Dict]:
        """Score candidate movies based on similar user interactions"""

        scored = {}
        for movie_id, interactions in candidate_movies.items():
            # Weighted average rating
            total_weight = 0
            weighted_rating = 0
            for user_id, similarity, rating in interactions:
                weight = similarity
                weighted_rating += rating * weight
                total_weight += weight

            avg_rating = weighted_rating / total_weight if total_weight > 0 else 0

            # Score based on:
            # - Number of similar users who liked it
            # - Average rating from similar users
            # - User similarity weights
            user_count = len(interactions)
            popularity_factor = min(1.0, user_count / 10)
            rating_factor = avg_rating / 10

            score = (popularity_factor * 0.4 + rating_factor * 0.6)
            score = min(1.0, max(0.0, score))

            scored[movie_id] = {
                "score": score,
                "similar_user_count": user_count,
                "avg_rating": round(avg_rating, 1),
                "total_weight": total_weight
            }

        return scored

    async def _popularity_fallback(
        self,
        context: RecommendationContext,
        count: int
    ) -> List[RecommendationResult]:
        """Fallback to popularity-based recommendations"""
        stmt = (
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(Movie.vote_average >= 7.0)
        )

        exclude_ids = set(context.exclude_movie_ids)
        if exclude_ids:
            stmt = stmt.where(Movie.id.notin_(exclude_ids))

        stmt = stmt.order_by(Movie.popularity.desc()).limit(count)

        result = await self.db.execute(stmt)
        movies = result.scalars().unique().all()

        results = []
        for i, movie in enumerate(movies):
            score = 0.7 - (i * 0.02)
            results.append(RecommendationResult(
                movie_id=movie.id,
                tmdb_id=movie.tmdb_id,
                title=movie.title,
                score=score,
                reasoning=f"Popular {movie.genres[0].name if movie.genres else ''} film loved by many.",
                source=self.name,
                metadata={"fallback": True}
            ))

        return results

    async def _get_movies_by_ids(self, movie_ids: List[int]) -> List[Movie]:
        """Get movies by IDs"""
        if not movie_ids:
            return []

        result = await self.db.execute(
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(Movie.id.in_(movie_ids))
        )
        return list(result.scalars().unique().all())

    def _generate_reasoning(
        self,
        movie: Movie,
        similar_user_count: int,
        avg_rating: float
    ) -> str:
        """Generate reasoning for collaborative recommendation"""
        genre = movie.genres[0].name if movie.genres else "film"

        if similar_user_count >= 5:
            return f"Loved by {similar_user_count} users with similar taste to yours, rated {avg_rating}/10 on average."
        else:
            return f"Recommended based on users who share your movie preferences, {avg_rating}/10 average rating."
