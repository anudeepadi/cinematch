"""
Content-based recommender using movie embeddings and user preference vectors.
"""

from typing import List, Dict
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.movie import Movie
from app.models.interaction import UserMovieInteraction
from app.services.recommenders.base import (
    BaseRecommender,
    RecommendationResult,
    UserPreferences,
    RecommendationContext
)
from app.tasks.embedding_generator import EmbeddingGenerator


class ContentBasedRecommender(BaseRecommender):
    """
    Content-based recommender using movie embeddings.

    Algorithm:
    1. Build user profile from liked/disliked movie embeddings
    2. Compute similarity between user profile and all movies
    3. Filter by context (genres, year, mood)
    4. Return top matches
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_generator = EmbeddingGenerator()

    @property
    def name(self) -> str:
        return "content_based"

    def get_weight(self, history_count: int) -> float:
        # Content-based works with any amount of history
        if history_count < 3:
            return 0.15
        elif history_count < 10:
            return 0.25
        else:
            return 0.30

    async def recommend(
        self,
        user_preferences: UserPreferences,
        context: RecommendationContext,
        count: int = 10
    ) -> List[RecommendationResult]:
        """Generate content-based recommendations"""

        # Get liked and disliked movies with embeddings
        liked_embeddings = await self._get_movie_embeddings(
            user_preferences.liked_movie_ids
        )
        disliked_embeddings = await self._get_movie_embeddings(
            user_preferences.disliked_movie_ids
        )

        # If no history, fall back to genre-based recommendations
        if not liked_embeddings:
            return await self._genre_based_recommendations(
                user_preferences, context, count
            )

        # Compute user preference embedding
        user_embedding = self.embedding_generator.compute_user_preference_embedding(
            liked_embeddings,
            disliked_embeddings
        )

        if user_embedding is None:
            return await self._genre_based_recommendations(
                user_preferences, context, count
            )

        # Get candidate movies
        candidates = await self._get_candidate_movies(
            user_preferences, context, count * 3
        )

        # Score candidates by similarity
        scored_candidates = []
        for movie in candidates:
            if movie.content_embedding:
                similarity = self.embedding_generator.compute_similarity(
                    user_embedding,
                    movie.content_embedding
                )

                # Apply mood boost
                mood_boost = self._calculate_mood_boost(movie, context.mood)

                # Apply genre boost
                genre_boost = self._calculate_genre_boost(
                    movie, user_preferences.genre_weights
                )

                final_score = similarity * 0.6 + mood_boost * 0.2 + genre_boost * 0.2
                scored_candidates.append((movie, final_score))

        # Sort by score and take top
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = scored_candidates[:count]

        # Build results
        results = []
        for movie, score in top_candidates:
            genre_names = [g.name for g in movie.genres]
            reasoning = self._generate_reasoning(movie, user_preferences, context)

            results.append(RecommendationResult(
                movie_id=movie.id,
                tmdb_id=movie.tmdb_id,
                title=movie.title,
                score=min(1.0, max(0.0, score)),
                reasoning=reasoning,
                source=self.name,
                metadata={
                    "genres": genre_names,
                    "year": movie.release_year,
                    "vote_average": movie.vote_average
                }
            ))

        return results

    async def _get_movie_embeddings(self, movie_ids: List[int]) -> List[List[float]]:
        """Get embeddings for a list of movie IDs"""
        if not movie_ids:
            return []

        result = await self.db.execute(
            select(Movie.content_embedding).where(
                Movie.id.in_(movie_ids),
                Movie.content_embedding.isnot(None)
            )
        )
        embeddings = [row[0] for row in result.all() if row[0]]
        return embeddings

    async def _get_candidate_movies(
        self,
        user_preferences: UserPreferences,
        context: RecommendationContext,
        limit: int
    ) -> List[Movie]:
        """Get candidate movies filtered by preferences and context"""
        stmt = (
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(Movie.content_embedding.isnot(None))
        )

        # Exclude already interacted movies
        exclude_ids = set(context.exclude_movie_ids)
        exclude_ids.update(user_preferences.watched_movie_ids)
        exclude_ids.update(user_preferences.liked_movie_ids)
        exclude_ids.update(user_preferences.disliked_movie_ids)

        if exclude_ids:
            stmt = stmt.where(Movie.id.notin_(exclude_ids))

        # Year range
        stmt = stmt.where(
            Movie.release_year >= user_preferences.year_range_min,
            Movie.release_year <= user_preferences.year_range_max
        )

        # Prefer new releases or classics if specified
        if context.prefer_new_releases:
            stmt = stmt.where(Movie.release_year >= 2020)
        elif context.prefer_classics:
            stmt = stmt.where(Movie.release_year <= 2000)

        # Order by popularity as tiebreaker
        stmt = stmt.order_by(Movie.popularity.desc()).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all())

    async def _genre_based_recommendations(
        self,
        user_preferences: UserPreferences,
        context: RecommendationContext,
        count: int
    ) -> List[RecommendationResult]:
        """Fallback to genre-based recommendations when no history"""
        stmt = (
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(Movie.vote_average >= 7.0)
            .order_by(Movie.popularity.desc())
            .limit(count)
        )

        result = await self.db.execute(stmt)
        movies = result.scalars().unique().all()

        results = []
        for i, movie in enumerate(movies):
            score = 0.8 - (i * 0.02)  # Decreasing score by rank
            results.append(RecommendationResult(
                movie_id=movie.id,
                tmdb_id=movie.tmdb_id,
                title=movie.title,
                score=score,
                reasoning=f"Highly rated {', '.join(g.name for g in movie.genres[:2])} movie with great reviews.",
                source=self.name,
                metadata={"genres": [g.name for g in movie.genres]}
            ))

        return results

    def _calculate_mood_boost(self, movie: Movie, mood: str) -> float:
        """Calculate boost based on mood match"""
        if not mood or not movie.mood_scores:
            return 0.5

        mood_mapping = {
            "excited": ["action", "thriller"],
            "relaxed": ["comedy", "drama"],
            "thoughtful": ["drama", "documentary"],
            "adventurous": ["action", "scifi"],
            "romantic": ["romance", "drama"],
            "scared": ["horror", "thriller"],
            "nostalgic": ["drama", "comedy"],
            "inspired": ["documentary", "drama"]
        }

        relevant_moods = mood_mapping.get(mood, [])
        if not relevant_moods:
            return 0.5

        scores = [movie.mood_scores.get(m, 0) for m in relevant_moods]
        return sum(scores) / len(scores) if scores else 0.5

    def _calculate_genre_boost(
        self,
        movie: Movie,
        genre_weights: Dict[int, float]
    ) -> float:
        """Calculate boost based on genre preferences"""
        if not genre_weights or not movie.genres:
            return 0.5

        genre_scores = []
        for genre in movie.genres:
            weight = genre_weights.get(str(genre.tmdb_id), 0.5)
            genre_scores.append(weight)

        return sum(genre_scores) / len(genre_scores) if genre_scores else 0.5

    def _generate_reasoning(
        self,
        movie: Movie,
        user_preferences: UserPreferences,
        context: RecommendationContext
    ) -> str:
        """Generate human-readable reasoning for recommendation"""
        reasons = []

        # Genre match
        if movie.genres:
            genre_names = [g.name for g in movie.genres[:2]]
            if user_preferences.preferred_genres:
                matching_genres = [
                    g.name for g in movie.genres
                    if g.tmdb_id in user_preferences.preferred_genres
                ]
                if matching_genres:
                    reasons.append(f"matches your love of {matching_genres[0]}")

        # Rating
        if movie.vote_average >= 8.0:
            reasons.append("critically acclaimed")
        elif movie.vote_average >= 7.0:
            reasons.append("well-received by audiences")

        # Mood match
        if context.mood and movie.mood_scores:
            mood_match = self._calculate_mood_boost(movie, context.mood)
            if mood_match > 0.7:
                reasons.append(f"great for your {context.mood} mood")

        # Year
        if movie.release_year:
            if movie.release_year >= 2023:
                reasons.append("recent release")
            elif movie.release_year <= 1990:
                reasons.append("classic film")

        if reasons:
            return f"This {movie.genres[0].name if movie.genres else 'film'} is {', '.join(reasons)}."
        else:
            return f"A {movie.vote_average:.1f}-rated {movie.genres[0].name if movie.genres else 'film'} you might enjoy."
