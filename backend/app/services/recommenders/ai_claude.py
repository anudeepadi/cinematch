"""
Claude AI recommender for nuanced, reasoning-based recommendations.
"""

import asyncio
import json
from typing import List, Optional
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


class ClaudeRecommender(BaseRecommender):
    """
    Claude-powered recommender for nuanced movie recommendations.

    Strengths:
    - Deep understanding of narrative and themes
    - Cultural context awareness
    - Excellent at explaining "why" a movie fits
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._client = None

    @property
    def name(self) -> str:
        return "claude"

    @property
    def client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    async def is_available(self) -> bool:
        return bool(settings.anthropic_api_key)

    def get_weight(self, history_count: int) -> float:
        return 0.20  # Consistent weight for AI quality

    async def recommend(
        self,
        user_preferences: UserPreferences,
        context: RecommendationContext,
        count: int = 10
    ) -> List[RecommendationResult]:
        """Generate recommendations using Claude"""

        if not await self.is_available():
            return []

        # Get candidate movies to recommend from
        candidates = await self._get_candidate_pool(user_preferences, context)
        if not candidates:
            return []

        # Build prompt
        prompt = self._build_prompt(user_preferences, context, candidates, count)

        try:
            # Run synchronous API call in thread pool with timeout
            def make_request():
                return self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )

            response = await asyncio.wait_for(
                asyncio.to_thread(make_request),
                timeout=AI_TIMEOUT
            )

            # Parse response
            return self._parse_response(response.content[0].text, candidates)

        except asyncio.TimeoutError:
            print(f"Claude API timeout after {AI_TIMEOUT}s")
            return []
        except Exception as e:
            print(f"Claude API error: {e}")
            return []

    async def _get_candidate_pool(
        self,
        user_preferences: UserPreferences,
        context: RecommendationContext,
        limit: int = 100
    ) -> List[Movie]:
        """Get a pool of candidate movies for Claude to choose from"""
        stmt = (
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(
                Movie.vote_average >= 6.0,
                Movie.vote_count >= 50
            )
        )

        # Exclude already seen movies
        exclude_ids = set(context.exclude_movie_ids)
        exclude_ids.update(user_preferences.watched_movie_ids)
        exclude_ids.update(user_preferences.liked_movie_ids)
        exclude_ids.update(user_preferences.disliked_movie_ids)

        if exclude_ids:
            stmt = stmt.where(Movie.id.notin_(exclude_ids))

        # Apply year range
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
        """Build the prompt for Claude"""

        # Format liked movies info
        liked_info = "No watch history yet" if not user_preferences.liked_movie_ids else \
            f"{len(user_preferences.liked_movie_ids)} movies liked"

        # Format genre preferences
        genre_prefs = "Not specified"
        if user_preferences.preferred_genres:
            genre_prefs = ", ".join(str(g) for g in user_preferences.preferred_genres[:5])

        # Format mood
        mood_info = context.mood or "not specified"

        # Format watching context
        watching_info = context.watching_with or "alone"

        # Format candidates
        candidate_list = []
        for m in candidates[:50]:  # Limit for token efficiency
            genres = ", ".join(g.name for g in m.genres[:3])
            candidate_list.append(
                f"- ID:{m.id} | {m.title} ({m.release_year}) | {genres} | {m.vote_average}/10 | {m.overview[:150] if m.overview else 'No overview'}..."
            )

        return f"""You are a film expert helping recommend movies. Based on the user's preferences and current context, select the {count} best movies from the candidate list.

USER PREFERENCES:
- History: {liked_info}
- Preferred genres: {genre_prefs}
- Year range: {user_preferences.year_range_min}-{user_preferences.year_range_max}
- Mood preferences: {user_preferences.mood_scores}

CURRENT CONTEXT:
- Current mood: {mood_info}
- Watching with: {watching_info}
- Prefer new releases: {context.prefer_new_releases}
- Prefer classics: {context.prefer_classics}

CANDIDATE MOVIES:
{chr(10).join(candidate_list)}

Return ONLY a JSON array with exactly {count} recommendations. Each recommendation must have:
- "id": the movie ID from the candidate list
- "score": confidence score 0.0-1.0
- "reasoning": 2-3 sentence explanation of why this movie fits the user

Example format:
[
  {{"id": 123, "score": 0.95, "reasoning": "This thriller perfectly matches your love of suspenseful films..."}},
  ...
]

Return ONLY the JSON array, no other text."""

    def _parse_response(
        self,
        response_text: str,
        candidates: List[Movie]
    ) -> List[RecommendationResult]:
        """Parse Claude's response into RecommendationResults"""
        results = []
        movie_map = {m.id: m for m in candidates}

        try:
            # Extract JSON from response
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
                            reasoning=rec.get("reasoning", "Recommended by Claude AI."),
                            source=self.name,
                            metadata={
                                "genres": [g.name for g in movie.genres],
                                "ai_model": "claude-sonnet-4-20250514"
                            }
                        ))

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Error parsing Claude response: {e}")

        return results
