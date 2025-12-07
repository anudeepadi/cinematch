"""
Ensemble recommender that aggregates all recommendation sources.

Uses weighted Borda count to combine recommendations from:
- Collaborative filtering
- Content-based filtering
- Claude AI
- OpenAI GPT
- Google Gemini
"""

import asyncio
import uuid
from typing import List, Dict, Optional
from collections import defaultdict
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.movie import Movie
from app.models.interaction import UserMovieInteraction, UserPreference
from app.models.recommendation import RecommendationSession
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationItem,
    RecommendationSource,
    RecommendationContext as ResponseContext
)
from app.schemas.movie import MovieListItem
from app.services.recommenders.base import (
    UserPreferences,
    RecommendationContext,
    RecommendationResult
)
from app.services.recommenders.content_based import ContentBasedRecommender
from app.services.recommenders.collaborative import CollaborativeFilteringRecommender
from app.services.recommenders.ai_claude import ClaudeRecommender
from app.services.recommenders.ai_openai import OpenAIRecommender
from app.services.recommenders.ai_gemini import GeminiRecommender
from app.services.recommenders.companion_merger import CompanionMerger, MergedPreferences
from app.services.recommenders.cold_start import ColdStartHandler


class EnsembleRecommender:
    """
    Aggregates recommendations from multiple sources using weighted Borda count.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.content_based = ContentBasedRecommender(db)
        self.collaborative = CollaborativeFilteringRecommender(db)
        self.claude = ClaudeRecommender(db)
        self.openai = OpenAIRecommender(db)
        self.gemini = GeminiRecommender(db)
        self.companion_merger = CompanionMerger()
        self.cold_start = ColdStartHandler(db)

    async def generate_recommendations(
        self,
        user: User,
        request: RecommendationRequest
    ) -> RecommendationResponse:
        """Generate recommendations using the ensemble approach"""

        # Build user preferences
        user_prefs = await self._build_user_preferences(user)

        # Build context
        context = self._build_context(request, user_prefs)

        # Handle companion preferences
        merged_prefs = None
        if request.companion_id:
            merged_prefs = await self._merge_companion_preferences(
                user_prefs, request.companion_id
            )
        elif request.companion_preferences:
            merged_prefs = self._merge_manual_companion(
                user_prefs, request.companion_preferences
            )

        # Apply merged preferences if available
        if merged_prefs:
            user_prefs = self._apply_merged_preferences(user_prefs, merged_prefs)

        # Check for cold start
        if user_prefs.history_count < 3:
            recommendations = await self.cold_start.get_cold_start_recommendations(
                user_prefs, context, request.count
            )
        else:
            # Get recommendations from all sources
            recommendations = await self._get_ensemble_recommendations(
                user_prefs, context, request.count
            )

        # Create session
        session = await self._create_session(user, request, recommendations, merged_prefs)

        # Build response
        return await self._build_response(session, recommendations, context, merged_prefs)

    async def _build_user_preferences(self, user: User) -> UserPreferences:
        """Build UserPreferences from user data"""

        # Get liked movies
        liked_result = await self.db.execute(
            select(UserMovieInteraction.movie_id).where(
                UserMovieInteraction.user_id == user.id,
                UserMovieInteraction.interaction_type.in_(["watch", "favorite"])
            )
        )
        liked_ids = [row[0] for row in liked_result.all()]

        # Get disliked movies
        disliked_result = await self.db.execute(
            select(UserMovieInteraction.movie_id).where(
                UserMovieInteraction.user_id == user.id,
                UserMovieInteraction.interaction_type == "pass"
            )
        )
        disliked_ids = [row[0] for row in disliked_result.all()]

        # Get watched movies
        watched_result = await self.db.execute(
            select(UserMovieInteraction.movie_id).where(
                UserMovieInteraction.user_id == user.id,
                UserMovieInteraction.interaction_type == "watched"
            )
        )
        watched_ids = [row[0] for row in watched_result.all()]

        # Get user preference weights
        pref_result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user.id)
        )
        user_pref = pref_result.scalar_one_or_none()

        genre_weights = {}
        if user_pref and user_pref.genre_weights:
            genre_weights = user_pref.genre_weights

        return UserPreferences(
            user_id=user.id,
            preferred_genres=user.preferred_genres or [],
            year_range_min=user.year_range_min,
            year_range_max=user.year_range_max,
            mood_scores={
                "action": user.mood_action,
                "comedy": user.mood_comedy,
                "drama": user.mood_drama,
                "horror": user.mood_horror,
                "romance": user.mood_romance,
                "scifi": user.mood_scifi,
                "thriller": user.mood_thriller,
                "documentary": user.mood_documentary
            },
            genre_weights=genre_weights,
            liked_movie_ids=liked_ids,
            disliked_movie_ids=disliked_ids,
            watched_movie_ids=watched_ids,
            history_count=len(liked_ids) + len(watched_ids)
        )

    def _build_context(
        self,
        request: RecommendationRequest,
        user_prefs: UserPreferences
    ) -> RecommendationContext:
        """Build recommendation context from request"""

        exclude_ids = list(set(
            user_prefs.liked_movie_ids +
            user_prefs.disliked_movie_ids +
            user_prefs.watched_movie_ids
        ))

        if request.exclude_genres:
            exclude_genres = request.exclude_genres
        else:
            exclude_genres = []

        return RecommendationContext(
            mood=request.mood,
            watching_with=request.watching_with,
            prefer_new_releases=request.prefer_new_releases or False,
            prefer_classics=request.prefer_classics or False,
            exclude_genres=exclude_genres,
            exclude_movie_ids=exclude_ids
        )

    async def _merge_companion_preferences(
        self,
        user_prefs: UserPreferences,
        companion_id: int
    ) -> Optional[MergedPreferences]:
        """Merge preferences with a linked companion"""

        companion_result = await self.db.execute(
            select(User).where(User.id == companion_id)
        )
        companion = companion_result.scalar_one_or_none()

        if not companion:
            return None

        return self.companion_merger.merge_preferences(
            user_genres=user_prefs.preferred_genres,
            user_year_min=user_prefs.year_range_min,
            user_year_max=user_prefs.year_range_max,
            user_moods=user_prefs.mood_scores,
            companion_genres=companion.preferred_genres or [],
            companion_year_min=companion.year_range_min,
            companion_year_max=companion.year_range_max,
            companion_moods={
                "action": companion.mood_action,
                "comedy": companion.mood_comedy,
                "drama": companion.mood_drama,
                "horror": companion.mood_horror,
                "romance": companion.mood_romance,
                "scifi": companion.mood_scifi,
                "thriller": companion.mood_thriller,
                "documentary": companion.mood_documentary
            }
        )

    def _merge_manual_companion(
        self,
        user_prefs: UserPreferences,
        companion_prefs
    ) -> MergedPreferences:
        """Merge with manually entered companion preferences"""

        return self.companion_merger.merge_preferences(
            user_genres=user_prefs.preferred_genres,
            user_year_min=user_prefs.year_range_min,
            user_year_max=user_prefs.year_range_max,
            user_moods=user_prefs.mood_scores,
            companion_genres=companion_prefs.preferred_genres,
            companion_year_min=companion_prefs.year_range_min or 1970,
            companion_year_max=companion_prefs.year_range_max or 2025,
            companion_moods=companion_prefs.mood_preferences,
            companion_disliked_genres=companion_prefs.disliked_genres
        )

    def _apply_merged_preferences(
        self,
        user_prefs: UserPreferences,
        merged: MergedPreferences
    ) -> UserPreferences:
        """Apply merged preferences to user preferences"""

        user_prefs.preferred_genres = merged.preferred_genres
        user_prefs.disliked_genres = merged.excluded_genres
        user_prefs.year_range_min = merged.year_range_min
        user_prefs.year_range_max = merged.year_range_max

        # Convert merged mood scores back to 1-5 scale
        for mood, score in merged.mood_scores.items():
            user_prefs.mood_scores[mood] = int(score * 5)

        return user_prefs

    async def _get_ensemble_recommendations(
        self,
        user_prefs: UserPreferences,
        context: RecommendationContext,
        count: int
    ) -> List[RecommendationResult]:
        """Get recommendations from all sources and aggregate"""

        # Determine which sources to use
        sources = [
            ("content_based", self.content_based),
            ("collaborative", self.collaborative)
        ]

        # Add AI sources if available
        if await self.claude.is_available():
            sources.append(("claude", self.claude))
        if await self.openai.is_available():
            sources.append(("openai", self.openai))
        if await self.gemini.is_available():
            sources.append(("gemini", self.gemini))

        # Get recommendations from all sources in parallel with overall timeout
        tasks = []
        for name, recommender in sources:
            tasks.append(
                recommender.recommend(user_prefs, context, count * 2)
            )

        try:
            # Wrap gather in a timeout to prevent hanging
            all_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=45  # 45 second total timeout for all recommenders
            )
        except asyncio.TimeoutError:
            print("Ensemble timeout - falling back to available results")
            all_results = [[] for _ in sources]

        # Aggregate results using weighted Borda count
        aggregated = self._weighted_borda_count(
            source_names=[name for name, _ in sources],
            all_recommendations=all_results,
            history_count=user_prefs.history_count
        )

        return aggregated[:count]

    def _weighted_borda_count(
        self,
        source_names: List[str],
        all_recommendations: List,
        history_count: int
    ) -> List[RecommendationResult]:
        """
        Aggregate recommendations using weighted Borda count.

        Each source assigns points based on rank position.
        Points are weighted by source weight.
        Movies appearing in multiple sources get diversity bonus.
        """

        # Movie scores: {movie_id: {score, sources, reasonings, metadata}}
        movie_data = defaultdict(lambda: {
            "score": 0.0,
            "sources": [],
            "reasonings": [],
            "best_result": None
        })

        for source_name, results in zip(source_names, all_recommendations):
            # Skip failed sources
            if isinstance(results, Exception) or not results:
                continue

            # Get source weight
            if hasattr(results[0], "source"):
                weight = self._get_source_weight(source_name, history_count)
            else:
                weight = 0.2

            # Assign Borda points
            n = len(results)
            for rank, rec in enumerate(results):
                if not isinstance(rec, RecommendationResult):
                    continue

                # Borda points: (n - rank) / n
                borda_points = (n - rank) / n
                weighted_score = borda_points * weight

                movie_id = rec.movie_id
                movie_data[movie_id]["score"] += weighted_score
                movie_data[movie_id]["sources"].append(rec.source)
                movie_data[movie_id]["reasonings"].append(rec.reasoning)

                # Keep best result for metadata
                if (movie_data[movie_id]["best_result"] is None or
                    rec.score > movie_data[movie_id]["best_result"].score):
                    movie_data[movie_id]["best_result"] = rec

        # Apply diversity bonus
        for movie_id, data in movie_data.items():
            unique_sources = len(set(data["sources"]))
            diversity_bonus = min(unique_sources * 0.05, 0.25)
            data["score"] += diversity_bonus

        # Sort by score
        sorted_movies = sorted(
            movie_data.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )

        # Build final results
        final_results = []
        for movie_id, data in sorted_movies:
            if data["best_result"]:
                result = data["best_result"]
                result.score = min(1.0, data["score"])

                # Combine reasoning if from multiple sources
                if len(set(data["sources"])) > 1:
                    result.reasoning = data["reasonings"][0]
                    result.metadata["sources"] = list(set(data["sources"]))

                final_results.append(result)

        return final_results

    def _get_source_weight(self, source_name: str, history_count: int) -> float:
        """Get weight for a source based on history count"""
        weights = {
            "collaborative": 0.10 if history_count < 10 else 0.30,
            "content_based": 0.25,
            "claude": 0.20,
            "openai": 0.15,
            "gemini": 0.15,
            "cold_start": 0.30,
            "trending": 0.20
        }
        return weights.get(source_name, 0.15)

    async def _create_session(
        self,
        user: User,
        request: RecommendationRequest,
        recommendations: List[RecommendationResult],
        merged_prefs: Optional[MergedPreferences]
    ) -> RecommendationSession:
        """Create and save recommendation session"""

        session = RecommendationSession(
            session_uuid=str(uuid.uuid4()),
            user_id=user.id,
            mood=request.mood,
            watching_with=request.watching_with,
            companion_id=request.companion_id,
            companion_preferences=request.companion_preferences.model_dump() if request.companion_preferences else None,
            prefer_new_releases=1 if request.prefer_new_releases else 0,
            prefer_classics=1 if request.prefer_classics else 0,
            exclude_genres=request.exclude_genres or [],
            recommendations=[
                {
                    "movie_id": r.movie_id,
                    "tmdb_id": r.tmdb_id,
                    "title": r.title,
                    "score": r.score,
                    "reasoning": r.reasoning,
                    "source": r.source
                }
                for r in recommendations
            ],
            total_candidates=len(recommendations),
            merged_preferences=merged_prefs.__dict__ if merged_prefs else None
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def _build_response(
        self,
        session: RecommendationSession,
        recommendations: List[RecommendationResult],
        context: RecommendationContext,
        merged_prefs: Optional[MergedPreferences]
    ) -> RecommendationResponse:
        """Build the final response"""

        # Get movie details
        movie_ids = [r.movie_id for r in recommendations]
        movie_result = await self.db.execute(
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(Movie.id.in_(movie_ids))
        )
        movies = {m.id: m for m in movie_result.scalars().unique().all()}

        # Build recommendation items
        items = []
        for rec in recommendations:
            movie = movies.get(rec.movie_id)
            if movie:
                items.append(RecommendationItem(
                    movie=MovieListItem(
                        id=movie.id,
                        tmdb_id=movie.tmdb_id,
                        title=movie.title,
                        overview=movie.overview,
                        release_year=movie.release_year,
                        vote_average=movie.vote_average,
                        poster_path=movie.poster_path,
                        poster_url=movie.poster_url,
                        backdrop_path=movie.backdrop_path,
                        backdrop_url=movie.backdrop_url,
                        genres=[{"id": g.id, "tmdb_id": g.tmdb_id, "name": g.name} for g in movie.genres]
                    ),
                    score=rec.score,
                    reasoning=rec.reasoning,
                    sources=[
                        RecommendationSource(
                            model=rec.source,
                            score=rec.score,
                            reasoning=rec.reasoning
                        )
                    ],
                    match_factors={k: float(v) for k, v in rec.metadata.items() if isinstance(v, (int, float))}
                ))

        return RecommendationResponse(
            session_id=session.session_uuid,
            recommendations=items,
            context=ResponseContext(
                mood=context.mood,
                watching_with=context.watching_with,
                companion_id=session.companion_id,
                used_companion_preferences=merged_prefs is not None,
                algorithm_weights={}
            ),
            total_candidates=session.total_candidates,
            generated_at=session.created_at
        )

    async def session_to_response(
        self,
        session: RecommendationSession
    ) -> RecommendationResponse:
        """Convert a saved session to response format"""

        recommendations = session.recommendations or []
        movie_ids = [r["movie_id"] for r in recommendations]

        movie_result = await self.db.execute(
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(Movie.id.in_(movie_ids))
        )
        movies = {m.id: m for m in movie_result.scalars().unique().all()}

        items = []
        for rec in recommendations:
            movie = movies.get(rec["movie_id"])
            if movie:
                items.append(RecommendationItem(
                    movie=MovieListItem(
                        id=movie.id,
                        tmdb_id=movie.tmdb_id,
                        title=movie.title,
                        overview=movie.overview,
                        release_year=movie.release_year,
                        vote_average=movie.vote_average,
                        poster_path=movie.poster_path,
                        poster_url=movie.poster_url,
                        backdrop_path=movie.backdrop_path,
                        backdrop_url=movie.backdrop_url,
                        genres=[{"id": g.id, "tmdb_id": g.tmdb_id, "name": g.name} for g in movie.genres]
                    ),
                    score=rec.get("score", 0.5),
                    reasoning=rec.get("reasoning", ""),
                    sources=[
                        RecommendationSource(
                            model=rec.get("source", "unknown"),
                            score=rec.get("score", 0.5),
                            reasoning=rec.get("reasoning")
                        )
                    ]
                ))

        return RecommendationResponse(
            session_id=session.session_uuid,
            recommendations=items,
            context=ResponseContext(
                mood=session.mood,
                watching_with=session.watching_with,
                companion_id=session.companion_id,
                used_companion_preferences=session.merged_preferences is not None
            ),
            total_candidates=session.total_candidates,
            generated_at=session.created_at
        )

    async def get_next_batch(
        self,
        session_id: str,
        user_id: int,
        count: int
    ) -> RecommendationResponse:
        """Get next batch of recommendations from existing session"""

        # Get session
        result = await self.db.execute(
            select(RecommendationSession).where(
                RecommendationSession.session_uuid == session_id,
                RecommendationSession.user_id == user_id
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("Session")

        # Get remaining recommendations
        all_recs = session.recommendations or []
        current_index = session.current_index or 0
        next_recs = all_recs[current_index:current_index + count]

        # Update session
        session.current_index = current_index + len(next_recs)
        session.recommendations_shown = (session.recommendations_shown or 0) + len(next_recs)
        await self.db.commit()

        # Build limited session for response
        session.recommendations = next_recs
        return await self.session_to_response(session)
