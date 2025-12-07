from datetime import datetime
from typing import Optional, List, Tuple, Dict
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.models.interaction import UserMovieInteraction, WatchHistory, UserPreference
from app.models.movie import Movie
from app.schemas.interaction import InteractionCreate, WatchHistoryCreate
from app.services.supabase_service import supabase_service, SupabaseService

logger = logging.getLogger(__name__)


class InteractionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._supabase_user_cache: Dict[int, str] = {}

    async def _get_supabase_user_id(self, user_id: int) -> Optional[str]:
        """Get or create Supabase user ID for a local user"""
        if user_id in self._supabase_user_cache:
            print(f"[SUPABASE] User {user_id} found in cache: {self._supabase_user_cache[user_id]}")
            return self._supabase_user_cache[user_id]

        if not SupabaseService.is_configured():
            print("[SUPABASE] Service not configured in _get_supabase_user_id")
            return None

        try:
            from app.models.user import User
            result = await self.db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                print(f"[SUPABASE] Local user {user_id} not found in database")
                return None

            print(f"[SUPABASE] Found local user: {user.email}, getting/creating in Supabase...")

            # Get or create user in Supabase
            supabase_user = await supabase_service.get_or_create_user(
                email=user.email,
                username=user.username
            )

            if supabase_user:
                supabase_id = supabase_user["id"]
                self._supabase_user_cache[user_id] = supabase_id
                print(f"[SUPABASE] Got Supabase user: {supabase_id}")
                return supabase_id
            else:
                print("[SUPABASE] get_or_create_user returned None")

        except Exception as e:
            print(f"[SUPABASE] Error getting Supabase user: {e}")
            import traceback
            traceback.print_exc()

        return None

    async def _sync_interaction_to_supabase(
        self,
        user_id: int,
        movie_id: int,
        interaction_type: str,
        context: Optional[Dict] = None
    ):
        """Sync interaction to Supabase (fire and forget)"""
        print(f"[SUPABASE] Starting sync for user={user_id}, movie={movie_id}, type={interaction_type}")

        if not SupabaseService.is_configured():
            print("[SUPABASE] Not configured, skipping sync")
            return

        try:
            print(f"[SUPABASE] Getting Supabase user ID for local user {user_id}")
            supabase_user_id = await self._get_supabase_user_id(user_id)
            if not supabase_user_id:
                print(f"[SUPABASE] Could not get Supabase user ID for user {user_id}")
                return

            print(f"[SUPABASE] Got Supabase user ID: {supabase_user_id}")

            # Get movie's TMDB ID
            result = await self.db.execute(select(Movie).where(Movie.id == movie_id))
            movie = result.scalar_one_or_none()
            tmdb_id = movie.tmdb_id if movie else movie_id

            print(f"[SUPABASE] Creating interaction in Supabase...")
            sync_result = await supabase_service.create_interaction(
                user_id=supabase_user_id,
                movie_id=movie_id,
                tmdb_id=tmdb_id,
                interaction_type=interaction_type,
                context=context
            )

            if sync_result:
                print(f"[SUPABASE] SUCCESS: Synced interaction - {sync_result}")
            else:
                print(f"[SUPABASE] WARNING: Sync returned None")

        except Exception as e:
            print(f"[SUPABASE] ERROR: {e}")
            import traceback
            traceback.print_exc()

    async def create_interaction(
        self,
        user_id: int,
        data: InteractionCreate
    ) -> UserMovieInteraction:
        """Create a new user-movie interaction"""
        # Check if interaction already exists
        result = await self.db.execute(
            select(UserMovieInteraction).where(
                UserMovieInteraction.user_id == user_id,
                UserMovieInteraction.movie_id == data.movie_id,
                UserMovieInteraction.interaction_type == data.interaction_type
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            # Update existing
            interaction = existing
            interaction.mood_at_interaction = data.mood_at_interaction
            interaction.watching_with = data.watching_with
            interaction.created_at = datetime.utcnow()
        else:
            interaction = UserMovieInteraction(
                user_id=user_id,
                movie_id=data.movie_id,
                interaction_type=data.interaction_type,
                mood_at_interaction=data.mood_at_interaction,
                watching_with=data.watching_with
            )
            self.db.add(interaction)

        await self.db.commit()
        await self.db.refresh(interaction)

        # Update user preferences based on interaction
        await self._update_preferences(user_id, data.movie_id, data.interaction_type)

        # Sync to Supabase (non-blocking)
        await self._sync_interaction_to_supabase(
            user_id=user_id,
            movie_id=data.movie_id,
            interaction_type=data.interaction_type,
            context={
                "mood": data.mood_at_interaction,
                "watching_with": data.watching_with
            }
        )

        return interaction

    async def add_to_watch_history(
        self,
        user_id: int,
        data: WatchHistoryCreate
    ) -> WatchHistory:
        """Add a movie to user's watch history"""
        # Check if already in history
        existing = await self.db.execute(
            select(WatchHistory).where(
                WatchHistory.user_id == user_id,
                WatchHistory.movie_id == data.movie_id
            )
        )
        history = existing.scalar_one_or_none()

        if history:
            # Update existing entry
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(history, field, value)
            history.watched_at = datetime.utcnow()
        else:
            history = WatchHistory(
                user_id=user_id,
                movie_id=data.movie_id,
                rating=data.rating,
                enjoyed=data.enjoyed,
                watched_with=data.watched_with,
                mood_before=data.mood_before,
                mood_after=data.mood_after,
                would_recommend=data.would_recommend,
                would_rewatch=data.would_rewatch,
                review=data.review,
                completed=data.completed,
                watch_percentage=data.watch_percentage
            )
            self.db.add(history)

        await self.db.commit()
        await self.db.refresh(history)

        # Also create a 'watched' interaction
        await self.create_interaction(
            user_id,
            InteractionCreate(
                movie_id=data.movie_id,
                interaction_type="watched",
                mood_at_interaction=data.mood_after,
                watching_with=data.watched_with
            )
        )

        return history

    async def get_user_interactions(
        self,
        user_id: int,
        interaction_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[UserMovieInteraction], int]:
        """Get user's interactions with pagination"""
        stmt = (
            select(UserMovieInteraction)
            .options(selectinload(UserMovieInteraction.movie).selectinload(Movie.genres))
            .where(UserMovieInteraction.user_id == user_id)
            .order_by(UserMovieInteraction.created_at.desc())
        )

        if interaction_type:
            stmt = stmt.where(UserMovieInteraction.interaction_type == interaction_type)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        interactions = list(result.scalars().all())

        return interactions, total

    async def get_watchlist(self, user_id: int) -> List[Movie]:
        """Get user's watchlist (movies marked as 'watch')"""
        result = await self.db.execute(
            select(Movie)
            .join(UserMovieInteraction)
            .options(selectinload(Movie.genres))
            .where(
                UserMovieInteraction.user_id == user_id,
                UserMovieInteraction.interaction_type == "watch"
            )
            .order_by(UserMovieInteraction.created_at.desc())
        )
        return list(result.scalars().unique().all())

    async def get_favorites(self, user_id: int) -> List[Movie]:
        """Get user's favorite movies"""
        result = await self.db.execute(
            select(Movie)
            .join(UserMovieInteraction)
            .options(selectinload(Movie.genres))
            .where(
                UserMovieInteraction.user_id == user_id,
                UserMovieInteraction.interaction_type == "favorite"
            )
            .order_by(UserMovieInteraction.created_at.desc())
        )
        return list(result.scalars().unique().all())

    async def get_watched(self, user_id: int) -> List[Movie]:
        """Get user's watched movies"""
        result = await self.db.execute(
            select(Movie)
            .join(UserMovieInteraction)
            .options(selectinload(Movie.genres))
            .where(
                UserMovieInteraction.user_id == user_id,
                UserMovieInteraction.interaction_type == "watched"
            )
            .order_by(UserMovieInteraction.created_at.desc())
        )
        return list(result.scalars().unique().all())

    async def get_watch_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[WatchHistory], int]:
        """Get user's watch history with pagination"""
        stmt = (
            select(WatchHistory)
            .where(WatchHistory.user_id == user_id)
            .order_by(WatchHistory.watched_at.desc())
        )

        count_result = await self.db.execute(
            select(func.count()).select_from(stmt.subquery())
        )
        total = count_result.scalar() or 0

        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        history = list(result.scalars().all())

        return history, total

    async def remove_from_watchlist(self, user_id: int, movie_id: int) -> bool:
        """Remove a movie from watchlist"""
        result = await self.db.execute(
            select(UserMovieInteraction).where(
                UserMovieInteraction.user_id == user_id,
                UserMovieInteraction.movie_id == movie_id,
                UserMovieInteraction.interaction_type == "watch"
            )
        )
        interaction = result.scalar_one_or_none()
        if interaction:
            await self.db.delete(interaction)
            await self.db.commit()
            return True
        return False

    async def get_passed_movie_ids(self, user_id: int) -> List[int]:
        """Get IDs of movies user has passed on"""
        result = await self.db.execute(
            select(UserMovieInteraction.movie_id).where(
                UserMovieInteraction.user_id == user_id,
                UserMovieInteraction.interaction_type == "pass"
            )
        )
        return [row[0] for row in result.all()]

    async def get_interacted_movie_ids(self, user_id: int) -> List[int]:
        """Get IDs of all movies user has interacted with"""
        result = await self.db.execute(
            select(UserMovieInteraction.movie_id).where(
                UserMovieInteraction.user_id == user_id
            ).distinct()
        )
        return [row[0] for row in result.all()]

    async def _update_preferences(
        self,
        user_id: int,
        movie_id: int,
        interaction_type: str
    ):
        """Update user preferences based on interaction"""
        # Get user preferences
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        prefs = result.scalar_one_or_none()
        if not prefs:
            prefs = UserPreference(user_id=user_id)
            self.db.add(prefs)

        # Update counts
        if interaction_type == "watched":
            prefs.total_watched = (prefs.total_watched or 0) + 1
        elif interaction_type == "pass":
            prefs.total_passed = (prefs.total_passed or 0) + 1
        elif interaction_type == "favorite":
            prefs.favorite_count = (prefs.favorite_count or 0) + 1

        # Update genre weights based on interaction
        movie_result = await self.db.execute(
            select(Movie).options(selectinload(Movie.genres)).where(Movie.id == movie_id)
        )
        movie = movie_result.scalar_one_or_none()

        if movie and movie.genres:
            genre_weights = dict(prefs.genre_weights) if prefs.genre_weights else {}

            # Positive weight for watch/favorite, negative for pass
            weight_delta = 0.1 if interaction_type in ["watch", "favorite", "watched"] else -0.1
            if interaction_type == "favorite":
                weight_delta = 0.2  # Extra weight for favorites

            for genre in movie.genres:
                current_weight = genre_weights.get(str(genre.tmdb_id), 0.5)
                new_weight = max(0, min(1, current_weight + weight_delta))
                genre_weights[str(genre.tmdb_id)] = new_weight

            prefs.genre_weights = genre_weights

        prefs.updated_at = datetime.utcnow()
        await self.db.commit()
