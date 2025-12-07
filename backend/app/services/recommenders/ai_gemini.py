"""
Google Gemini recommender for recent and trending awareness.
"""

import json
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.movie import Movie
from app.services.recommenders.base import (
    BaseRecommender,
    RecommendationResult,
    UserPreferences,
    RecommendationContext
)


class GeminiRecommender(BaseRecommender):
    """
    Google Gemini-powered recommender.

    Strengths:
    - Recent knowledge of new releases
    - Multi-modal understanding
    - Good at trending awareness
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._model = None

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def model(self):
        if self._model is None:
            import google.generativeai as genai
            genai.configure(api_key=settings.google_api_key)
            self._model = genai.GenerativeModel('gemini-1.5-flash')
        return self._model

    async def is_available(self) -> bool:
        return bool(settings.google_api_key)

    def get_weight(self, history_count: int) -> float:
        return 0.15

    async def recommend(
        self,
        user_preferences: UserPreferences,
        context: RecommendationContext,
        count: int = 10
    ) -> List[RecommendationResult]:
        """Generate recommendations using Gemini"""

        if not await self.is_available():
            return []

        candidates = await self._get_candidate_pool(user_preferences, context)
        if not candidates:
            return []

        prompt = self._build_prompt(user_preferences, context, candidates, count)

        try:
            response = self.model.generate_content(prompt)
            return self._parse_response(response.text, candidates)

        except Exception as e:
            print(f"Gemini API error: {e}")
            return []

    async def _get_candidate_pool(
        self,
        user_preferences: UserPreferences,
        context: RecommendationContext,
        limit: int = 100
    ) -> List[Movie]:
        """Get candidate movies"""
        stmt = (
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(
                Movie.vote_average >= 6.0,
                Movie.vote_count >= 50
            )
        )

        exclude_ids = set(context.exclude_movie_ids)
        exclude_ids.update(user_preferences.watched_movie_ids)
        exclude_ids.update(user_preferences.liked_movie_ids)
        exclude_ids.update(user_preferences.disliked_movie_ids)

        if exclude_ids:
            stmt = stmt.where(Movie.id.notin_(exclude_ids))

        stmt = stmt.where(
            Movie.release_year >= user_preferences.year_range_min,
            Movie.release_year <= user_preferences.year_range_max
        )

        # Gemini focuses on newer movies
        if context.prefer_new_releases:
            stmt = stmt.where(Movie.release_year >= 2022)

        stmt = stmt.order_by(Movie.popularity.desc()).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all())

    def _build_prompt(
        self,
        user_preferences: UserPreferences,
        context: RecommendationContext,
        candidates: List[Movie],
        count: int
    ) -> str:
        """Build the prompt for Gemini"""

        candidate_list = []
        for m in candidates[:50]:
            genres = ", ".join(g.name for g in m.genres[:3])
            candidate_list.append(
                f"ID:{m.id} | {m.title} ({m.release_year}) | {genres} | {m.vote_average}/10"
            )

        mood_info = context.mood or "not specified"
        watching_info = context.watching_with or "alone"

        return f"""You are a movie recommendation expert. Select the best {count} movies from this list.

User context:
- Current mood: {mood_info}
- Watching with: {watching_info}
- Year preference: {user_preferences.year_range_min}-{user_preferences.year_range_max}

Available movies:
{chr(10).join(candidate_list)}

Respond with ONLY a JSON array:
[{{"id": movie_id, "score": 0.0-1.0, "reasoning": "brief explanation"}}]

No other text, just the JSON array."""

    def _parse_response(
        self,
        response_text: str,
        candidates: List[Movie]
    ) -> List[RecommendationResult]:
        """Parse Gemini response"""
        results = []
        movie_map = {m.id: m for m in candidates}

        try:
            # Clean response
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            json_start = text.find('[')
            json_end = text.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = text[json_start:json_end]
                recommendations = json.loads(json_str)

                for rec in recommendations:
                    movie_id = rec.get("id")
                    movie = movie_map.get(movie_id)

                    if movie:
                        results.append(RecommendationResult(
                            movie_id=movie.id,
                            tmdb_id=movie.tmdb_id,
                            title=movie.title,
                            score=float(rec.get("score", 0.7)),
                            reasoning=rec.get("reasoning", "Recommended by Gemini."),
                            source=self.name,
                            metadata={
                                "genres": [g.name for g in movie.genres],
                                "ai_model": "gemini-1.5-flash"
                            }
                        ))

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Error parsing Gemini response: {e}")

        return results
