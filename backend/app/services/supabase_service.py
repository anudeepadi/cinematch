from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from supabase import create_client, Client

from app.config import settings

logger = logging.getLogger(__name__)


class SupabaseService:
    """Service for interacting with Supabase database"""

    _client: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Optional[Client]:
        """Get or create Supabase client"""
        if cls._client is None:
            if not settings.supabase_url or not settings.supabase_key:
                logger.warning("Supabase credentials not configured")
                return None
            try:
                cls._client = create_client(
                    settings.supabase_url,
                    settings.supabase_key
                )
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                return None
        return cls._client

    @classmethod
    def is_configured(cls) -> bool:
        """Check if Supabase is properly configured"""
        return bool(settings.supabase_url and settings.supabase_key)

    # User operations
    async def get_or_create_user(
        self,
        email: str,
        username: str,
        auth_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Get or create a user in Supabase"""
        client = self.get_client()
        if not client:
            return None

        try:
            # Try to find existing user by email
            result = client.table("users").select("*").eq("email", email).execute()

            if result.data:
                return result.data[0]

            # Create new user
            user_data = {
                "email": email,
                "username": username,
                "auth_id": auth_id,
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            result = client.table("users").insert(user_data).execute()

            if result.data:
                # Also create default preferences
                user_id = result.data[0]["id"]
                client.table("user_preferences").insert({
                    "user_id": user_id,
                    "updated_at": datetime.utcnow().isoformat()
                }).execute()

            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error in get_or_create_user: {e}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        client = self.get_client()
        if not client:
            return None

        try:
            result = client.table("users").select("*").eq("email", email).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None

    async def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """Update user preferences"""
        client = self.get_client()
        if not client:
            return False

        try:
            preferences["updated_at"] = datetime.utcnow().isoformat()
            client.table("users").update(preferences).eq("id", user_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False

    # Movie interaction operations
    async def create_interaction(
        self,
        user_id: str,
        movie_id: int,
        tmdb_id: int,
        interaction_type: str,
        rating: Optional[float] = None,
        context: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Create a movie interaction record"""
        client = self.get_client()
        if not client:
            return None

        try:
            data = {
                "user_id": user_id,
                "movie_id": movie_id,
                "tmdb_id": tmdb_id,
                "interaction_type": interaction_type,
                "rating": rating,
                "context": context or {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            result = client.table("user_movie_interactions").insert(data).execute()

            # Update user preferences stats
            await self._update_preference_stats(user_id, interaction_type)

            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error creating interaction: {e}")
            return None

    async def get_user_interactions(
        self,
        user_id: str,
        interaction_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """Get user's movie interactions"""
        client = self.get_client()
        if not client:
            return []

        try:
            query = client.table("user_movie_interactions").select("*").eq("user_id", user_id)

            if interaction_type:
                query = query.eq("interaction_type", interaction_type)

            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
            result = query.execute()

            return result.data or []

        except Exception as e:
            logger.error(f"Error getting interactions: {e}")
            return []

    async def get_interacted_movie_ids(
        self,
        user_id: str,
        interaction_types: Optional[List[str]] = None
    ) -> List[int]:
        """Get list of movie IDs user has interacted with"""
        client = self.get_client()
        if not client:
            return []

        try:
            query = client.table("user_movie_interactions").select("movie_id").eq("user_id", user_id)

            if interaction_types:
                query = query.in_("interaction_type", interaction_types)

            result = query.execute()
            return list(set([item["movie_id"] for item in result.data])) if result.data else []

        except Exception as e:
            logger.error(f"Error getting interacted movie IDs: {e}")
            return []

    async def remove_interaction(
        self,
        user_id: str,
        movie_id: int,
        interaction_type: str
    ) -> bool:
        """Remove a specific interaction"""
        client = self.get_client()
        if not client:
            return False

        try:
            client.table("user_movie_interactions").delete().eq(
                "user_id", user_id
            ).eq(
                "movie_id", movie_id
            ).eq(
                "interaction_type", interaction_type
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Error removing interaction: {e}")
            return False

    # Recommendation session operations
    async def create_recommendation_session(
        self,
        user_id: str,
        session_uuid: str,
        mood: Optional[str] = None,
        watching_with: Optional[str] = None,
        recommendations: Optional[List[Dict]] = None,
        algorithm_weights: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Create a recommendation session"""
        client = self.get_client()
        if not client:
            return None

        try:
            data = {
                "user_id": user_id,
                "session_uuid": session_uuid,
                "mood": mood,
                "watching_with": watching_with,
                "recommendations": recommendations or [],
                "algorithm_weights": algorithm_weights or {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            result = client.table("recommendation_sessions").insert(data).execute()
            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error creating recommendation session: {e}")
            return None

    async def update_recommendation_session(
        self,
        session_uuid: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update a recommendation session"""
        client = self.get_client()
        if not client:
            return False

        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            client.table("recommendation_sessions").update(updates).eq(
                "session_uuid", session_uuid
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating recommendation session: {e}")
            return False

    async def get_recommendation_session(self, session_uuid: str) -> Optional[Dict]:
        """Get a recommendation session by UUID"""
        client = self.get_client()
        if not client:
            return None

        try:
            result = client.table("recommendation_sessions").select("*").eq(
                "session_uuid", session_uuid
            ).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting recommendation session: {e}")
            return None

    # Helper methods
    async def _update_preference_stats(self, user_id: str, interaction_type: str):
        """Update user preference statistics"""
        client = self.get_client()
        if not client:
            return

        try:
            # Get current preferences
            result = client.table("user_preferences").select("*").eq("user_id", user_id).execute()

            if not result.data:
                # Create preferences if not exist
                client.table("user_preferences").insert({
                    "user_id": user_id,
                    "total_watched": 1 if interaction_type == "watched" else 0,
                    "total_passed": 1 if interaction_type == "pass" else 0,
                    "favorite_count": 1 if interaction_type == "favorite" else 0,
                    "updated_at": datetime.utcnow().isoformat()
                }).execute()
            else:
                prefs = result.data[0]
                updates = {"updated_at": datetime.utcnow().isoformat()}

                if interaction_type == "watched":
                    updates["total_watched"] = (prefs.get("total_watched") or 0) + 1
                elif interaction_type == "pass":
                    updates["total_passed"] = (prefs.get("total_passed") or 0) + 1
                elif interaction_type == "favorite":
                    updates["favorite_count"] = (prefs.get("favorite_count") or 0) + 1

                client.table("user_preferences").update(updates).eq("user_id", user_id).execute()

        except Exception as e:
            logger.error(f"Error updating preference stats: {e}")

    # Companion operations
    async def create_companion_link(
        self,
        user_id: str,
        companion_id: str,
        nickname: Optional[str] = None
    ) -> Optional[Dict]:
        """Create a companion link request"""
        client = self.get_client()
        if not client:
            return None

        try:
            data = {
                "user_id": user_id,
                "companion_id": companion_id,
                "status": "pending",
                "nickname": nickname,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            result = client.table("companion_links").insert(data).execute()
            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error creating companion link: {e}")
            return None

    async def update_companion_link_status(
        self,
        link_id: str,
        status: str
    ) -> bool:
        """Update companion link status"""
        client = self.get_client()
        if not client:
            return False

        try:
            updates = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            if status == "accepted":
                updates["accepted_at"] = datetime.utcnow().isoformat()

            client.table("companion_links").update(updates).eq("id", link_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating companion link: {e}")
            return False

    async def get_user_companions(self, user_id: str) -> List[Dict]:
        """Get user's accepted companions"""
        client = self.get_client()
        if not client:
            return []

        try:
            # Get companions where user is either the requester or the companion
            result = client.table("companion_links").select("*").eq(
                "status", "accepted"
            ).or_(f"user_id.eq.{user_id},companion_id.eq.{user_id}").execute()

            return result.data or []
        except Exception as e:
            logger.error(f"Error getting companions: {e}")
            return []


# Global instance
supabase_service = SupabaseService()
