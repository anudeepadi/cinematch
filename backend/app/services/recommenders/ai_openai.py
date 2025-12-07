"""
OpenAI GPT recommender for knowledge-rich recommendations.
"""

import asyncio
import json
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings

# Timeout for AI API calls (in seconds)
AI_TIMEOUT = 30
from app.models.movie import Movie
from app.services.recommenders.base import (
    BaseRecommender,
    RecommendationResult,
    UserPreferences,
    RecommendationContext
)


class OpenAIRecommender(BaseRecommender):
    """
    OpenAI GPT-powered recommender.

    Strengths:
    - Broad movie knowledge
    - Good at understanding obscure films
    - Strong general reasoning
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._client = None

    @property
    def name(self) -> str:
        return "openai"

    @property
    def client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=settings.openai_api_key)
        return self._client

    async def is_available(self) -> bool:
        return bool(settings.openai_api_key)

    def get_weight(self, history_count: int) -> float:
        return 0.15

    async def recommend(
        self,
        user_preferences: UserPreferences,
        context: RecommendationContext,
        count: int = 10
    ) -> List[RecommendationResult]:
        """Generate recommendations using OpenAI GPT"""

        if not await self.is_available():
            return []

        candidates = await self._get_candidate_pool(user_preferences, context)
        if not candidates:
            return []

        prompt = self._build_prompt(user_preferences, context, candidates, count)

        try:
            # Run synchronous API call in thread pool with timeout
            def make_request():
                return self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a film expert. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.7
                )

            response = await asyncio.wait_for(
                asyncio.to_thread(make_request),
                timeout=AI_TIMEOUT
            )

            return self._parse_response(
                response.choices[0].message.content,
                candidates
            )

        except asyncio.TimeoutError:
            print(f"OpenAI API timeout after {AI_TIMEOUT}s")
            return []
        except Exception as e:
            print(f"OpenAI API error: {e}")
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
        """Build the prompt for GPT"""

        candidate_list = []
        for m in candidates[:50]:
            genres = ", ".join(g.name for g in m.genres[:3])
            candidate_list.append(
                f"ID:{m.id} | {m.title} ({m.release_year}) | {genres} | {m.vote_average}/10"
            )

        mood_info = context.mood or "not specified"
        watching_info = context.watching_with or "alone"

        return f"""Select {count} movies from this list for a user with these preferences:

Mood: {mood_info}
Watching: {watching_info}
Preferred years: {user_preferences.year_range_min}-{user_preferences.year_range_max}
Mood preferences: {user_preferences.mood_scores}

MOVIES:
{chr(10).join(candidate_list)}

Return JSON array only:
[{{"id": movie_id, "score": 0.0-1.0, "reasoning": "why this fits"}}]"""

    def _parse_response(
        self,
        response_text: str,
        candidates: List[Movie]
    ) -> List[RecommendationResult]:
        """Parse GPT response"""
        results = []
        movie_map = {m.id: m for m in candidates}

        try:
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
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
                            reasoning=rec.get("reasoning", "Recommended by GPT."),
                            source=self.name,
                            metadata={
                                "genres": [g.name for g in movie.genres],
                                "ai_model": "gpt-4o-mini"
                            }
                        ))

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Error parsing OpenAI response: {e}")

        return results
