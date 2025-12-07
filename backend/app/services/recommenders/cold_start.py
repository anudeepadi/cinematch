"""
Cold start handler for new users with no history.
"""

from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.movie import Movie, Genre
from app.services.recommenders.base import (
    RecommendationResult,
    UserPreferences,
    RecommendationContext
)


class ColdStartHandler:
    """
    Handles recommendations for new users with no history.

    Strategies:
    1. Quick preference quiz
    2. Popular movies bootstrap
    3. Genre-based exploration
    4. Trending content
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_onboarding_movies(
        self,
        count: int = 20
    ) -> List[Movie]:
        """Get diverse popular movies for onboarding quiz"""

        # Get movies that are:
        # - Highly rated
        # - Popular
        # - Diverse genres
        result = await self.db.execute(
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(
                Movie.vote_count >= 1000,
                Movie.vote_average >= 7.0
            )
            .order_by(Movie.popularity.desc())
            .limit(count * 2)  # Get more to filter for diversity
        )

        movies = list(result.scalars().unique().all())

        # Ensure genre diversity
        return self._ensure_genre_diversity(movies, count)

    def _ensure_genre_diversity(
        self,
        movies: List[Movie],
        count: int
    ) -> List[Movie]:
        """Select movies ensuring genre diversity"""
        selected = []
        genre_counts = {}

        for movie in movies:
            if len(selected) >= count:
                break

            # Check genre representation
            movie_genres = [g.tmdb_id for g in movie.genres]
            max_genre_count = max(
                (genre_counts.get(g, 0) for g in movie_genres),
                default=0
            )

            # Allow up to 3 movies per genre
            if max_genre_count < 3:
                selected.append(movie)
                for g in movie_genres:
                    genre_counts[g] = genre_counts.get(g, 0) + 1

        return selected

    async def get_cold_start_recommendations(
        self,
        user_preferences: UserPreferences,
        context: RecommendationContext,
        count: int = 10
    ) -> List[RecommendationResult]:
        """
        Generate recommendations for new users based on stated preferences.
        """

        # Build query based on stated preferences
        stmt = (
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(Movie.vote_average >= 6.5)
        )

        # Apply genre filter if user has preferences
        if user_preferences.preferred_genres:
            stmt = stmt.join(Movie.genres).where(
                Genre.tmdb_id.in_(user_preferences.preferred_genres)
            )

        # Apply year range
        stmt = stmt.where(
            Movie.release_year >= user_preferences.year_range_min,
            Movie.release_year <= user_preferences.year_range_max
        )

        # Exclude already seen
        exclude_ids = set(context.exclude_movie_ids)
        if exclude_ids:
            stmt = stmt.where(Movie.id.notin_(exclude_ids))

        # Order by popularity (good for cold start)
        stmt = stmt.order_by(Movie.popularity.desc()).limit(count * 2)

        result = await self.db.execute(stmt)
        movies = list(result.scalars().unique().all())

        # Apply mood filtering if specified
        if context.mood:
            movies = self._filter_by_mood(movies, context.mood)

        # Build results
        results = []
        for i, movie in enumerate(movies[:count]):
            score = 0.85 - (i * 0.02)  # Decreasing score by rank
            reasoning = self._generate_cold_start_reasoning(
                movie, user_preferences, context
            )

            results.append(RecommendationResult(
                movie_id=movie.id,
                tmdb_id=movie.tmdb_id,
                title=movie.title,
                score=score,
                reasoning=reasoning,
                source="cold_start",
                metadata={
                    "genres": [g.name for g in movie.genres],
                    "year": movie.release_year,
                    "vote_average": movie.vote_average
                }
            ))

        return results

    def _filter_by_mood(
        self,
        movies: List[Movie],
        mood: str
    ) -> List[Movie]:
        """Filter movies by mood match"""
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
            return movies

        scored_movies = []
        for movie in movies:
            if movie.mood_scores:
                mood_score = sum(
                    movie.mood_scores.get(m, 0)
                    for m in relevant_moods
                ) / len(relevant_moods)
                scored_movies.append((movie, mood_score))
            else:
                scored_movies.append((movie, 0.5))

        scored_movies.sort(key=lambda x: x[1], reverse=True)
        return [m for m, _ in scored_movies]

    def _generate_cold_start_reasoning(
        self,
        movie: Movie,
        user_preferences: UserPreferences,
        context: RecommendationContext
    ) -> str:
        """Generate reasoning for cold start recommendation"""
        reasons = []

        # Genre match
        if movie.genres and user_preferences.preferred_genres:
            matching = [
                g.name for g in movie.genres
                if g.tmdb_id in user_preferences.preferred_genres
            ]
            if matching:
                reasons.append(f"matches your interest in {matching[0]}")

        # Rating
        if movie.vote_average >= 8.0:
            reasons.append("critically acclaimed")
        elif movie.vote_average >= 7.5:
            reasons.append("highly rated")

        # Popularity
        if movie.popularity > 100:
            reasons.append("popular choice")

        # Mood
        if context.mood:
            reasons.append(f"good for a {context.mood} mood")

        if reasons:
            genre = movie.genres[0].name if movie.genres else "film"
            return f"This {genre} is {', '.join(reasons)}."
        else:
            return f"A well-rated {movie.genres[0].name if movie.genres else 'film'} to start your journey."

    async def get_trending_recommendations(
        self,
        count: int = 10
    ) -> List[RecommendationResult]:
        """Get trending movie recommendations"""
        result = await self.db.execute(
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(
                Movie.release_year >= 2023,
                Movie.vote_average >= 6.0
            )
            .order_by(Movie.popularity.desc())
            .limit(count)
        )

        movies = result.scalars().unique().all()
        results = []

        for i, movie in enumerate(movies):
            score = 0.9 - (i * 0.02)
            results.append(RecommendationResult(
                movie_id=movie.id,
                tmdb_id=movie.tmdb_id,
                title=movie.title,
                score=score,
                reasoning=f"Currently trending {movie.genres[0].name if movie.genres else ''} film.",
                source="trending",
                metadata={"genres": [g.name for g in movie.genres]}
            ))

        return results
