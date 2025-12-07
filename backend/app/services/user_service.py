from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.interaction import UserPreference
from app.schemas.user import UserUpdate, UserPreferencesUpdate, OnboardingPreferences
from app.core.exceptions import NotFoundError


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_user(self, user: User, data: UserUpdate) -> User:
        """Update user profile"""
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(user, field, value)

        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_preferences(self, user: User, data: UserPreferencesUpdate) -> User:
        """Update user preferences directly on user model"""
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)

        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_user_preferences(self, user_id: int) -> Optional[UserPreference]:
        """Get detailed user preferences"""
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_user_preferences(self, user_id: int) -> UserPreference:
        """Create initial user preferences"""
        preferences = UserPreference(user_id=user_id)
        self.db.add(preferences)
        await self.db.commit()
        await self.db.refresh(preferences)
        return preferences

    async def update_learned_preferences(
        self,
        user_id: int,
        genre_weights: Optional[Dict[int, float]] = None,
        actor_preferences: Optional[Dict[int, float]] = None,
        director_preferences: Optional[Dict[int, float]] = None,
        keyword_preferences: Optional[Dict[str, float]] = None
    ) -> UserPreference:
        """Update learned preferences from user interactions"""
        prefs = await self.get_user_preferences(user_id)
        if not prefs:
            prefs = await self.create_user_preferences(user_id)

        if genre_weights is not None:
            prefs.genre_weights = genre_weights
        if actor_preferences is not None:
            prefs.actor_preferences = actor_preferences
        if director_preferences is not None:
            prefs.director_preferences = director_preferences
        if keyword_preferences is not None:
            prefs.keyword_preferences = keyword_preferences

        prefs.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(prefs)
        return prefs

    async def process_onboarding(
        self,
        user: User,
        data: OnboardingPreferences
    ) -> User:
        """Process onboarding preferences and set up user"""
        # Update user's genre preferences
        user.preferred_genres = data.preferred_genres

        # Set year preferences based on selection
        if data.year_preference == "classics":
            user.year_range_min = 1950
            user.year_range_max = 1999
        elif data.year_preference == "modern":
            user.year_range_min = 2000
            user.year_range_max = 2025
        else:  # "all"
            user.year_range_min = 1950
            user.year_range_max = 2025

        # Set preferred decades
        if data.preferred_decades:
            prefs = await self.get_user_preferences(user.id)
            if prefs:
                prefs.preferred_decades = data.preferred_decades
                await self.db.commit()

        # Process mood preferences
        mood_mapping = {
            "action": "mood_action",
            "comedy": "mood_comedy",
            "drama": "mood_drama",
            "horror": "mood_horror",
            "romance": "mood_romance",
            "scifi": "mood_scifi",
            "thriller": "mood_thriller",
            "documentary": "mood_documentary"
        }

        for mood, value in data.mood_preferences.items():
            if mood.lower() in mood_mapping:
                setattr(user, mood_mapping[mood.lower()], value)

        # Mark user as onboarded
        user.is_onboarded = True
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def get_user_mood_preferences(self, user: User) -> Dict[str, int]:
        """Get user's mood preferences as a dictionary"""
        return {
            "action": user.mood_action,
            "comedy": user.mood_comedy,
            "drama": user.mood_drama,
            "horror": user.mood_horror,
            "romance": user.mood_romance,
            "scifi": user.mood_scifi,
            "thriller": user.mood_thriller,
            "documentary": user.mood_documentary
        }
