from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class UserResponse(BaseModel):
    """Full user profile response"""
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferred_genres: List[int] = []
    year_range_min: int = 1970
    year_range_max: int = 2025
    preferred_languages: List[str] = ["en"]
    mood_action: int = 3
    mood_comedy: int = 3
    mood_drama: int = 3
    mood_horror: int = 3
    mood_romance: int = 3
    mood_scifi: int = 3
    mood_thriller: int = 3
    mood_documentary: int = 3
    watch_alone_preference: int = 3
    is_active: bool = True
    is_verified: bool = False
    is_onboarded: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=500)
    preferred_languages: Optional[List[str]] = None


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences"""
    preferred_genres: Optional[List[int]] = None
    year_range_min: Optional[int] = Field(None, ge=1900, le=2030)
    year_range_max: Optional[int] = Field(None, ge=1900, le=2030)
    mood_action: Optional[int] = Field(None, ge=1, le=5)
    mood_comedy: Optional[int] = Field(None, ge=1, le=5)
    mood_drama: Optional[int] = Field(None, ge=1, le=5)
    mood_horror: Optional[int] = Field(None, ge=1, le=5)
    mood_romance: Optional[int] = Field(None, ge=1, le=5)
    mood_scifi: Optional[int] = Field(None, ge=1, le=5)
    mood_thriller: Optional[int] = Field(None, ge=1, le=5)
    mood_documentary: Optional[int] = Field(None, ge=1, le=5)
    watch_alone_preference: Optional[int] = Field(None, ge=1, le=5)


class UserPreferencesResponse(BaseModel):
    """Response schema for detailed user preferences"""
    id: int
    user_id: int
    genre_weights: Dict[int, float] = {}
    preferred_decades: List[int] = []
    new_releases_interest: float = 0.5
    classics_interest: float = 0.5
    actor_preferences: Dict[int, float] = {}
    director_preferences: Dict[int, float] = {}
    keyword_preferences: Dict[str, float] = {}
    avg_rating: Optional[float] = None
    total_watched: int = 0
    total_passed: int = 0
    favorite_count: int = 0
    updated_at: datetime

    class Config:
        from_attributes = True


class OnboardingPreferences(BaseModel):
    """Schema for new user onboarding preferences"""
    preferred_genres: List[int] = Field(..., min_length=1, max_length=10)
    preferred_decades: List[int] = Field(default_factory=list)
    mood_preferences: Dict[str, int] = Field(default_factory=dict)
    favorite_movies: Optional[List[int]] = Field(None, max_length=20)
    year_preference: Optional[str] = None  # "classics", "modern", "all"


class MoodPreferences(BaseModel):
    """Current mood for recommendation session"""
    action: int = Field(default=3, ge=1, le=5)
    comedy: int = Field(default=3, ge=1, le=5)
    drama: int = Field(default=3, ge=1, le=5)
    horror: int = Field(default=3, ge=1, le=5)
    romance: int = Field(default=3, ge=1, le=5)
    scifi: int = Field(default=3, ge=1, le=5)
    thriller: int = Field(default=3, ge=1, le=5)
    documentary: int = Field(default=3, ge=1, le=5)
