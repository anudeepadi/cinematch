from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

from app.schemas.movie import MovieListItem


class InteractionCreate(BaseModel):
    """Schema for creating a new interaction"""
    movie_id: int
    interaction_type: Literal['watch', 'pass', 'favorite', 'watched']
    mood_at_interaction: Optional[str] = None
    watching_with: Optional[Literal['alone', 'partner', 'friends', 'family']] = None
    session_id: Optional[str] = Field(None, description="Recommendation session this interaction came from")


class InteractionResponse(BaseModel):
    """Response schema for an interaction"""
    id: int
    user_id: int
    movie_id: int
    interaction_type: str
    rating: Optional[float] = None
    mood_at_interaction: Optional[str] = None
    watching_with: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InteractionWithMovie(BaseModel):
    """Interaction with movie details"""
    id: int
    interaction_type: str
    rating: Optional[float] = None
    mood_at_interaction: Optional[str] = None
    watching_with: Optional[str] = None
    created_at: datetime
    movie: MovieListItem

    class Config:
        from_attributes = True


class WatchHistoryCreate(BaseModel):
    """Schema for adding to watch history"""
    movie_id: int
    rating: Optional[float] = Field(None, ge=1, le=10)
    enjoyed: Optional[bool] = None
    watched_with: Optional[Literal['alone', 'partner', 'friends', 'family']] = None
    mood_before: Optional[str] = None
    mood_after: Optional[str] = None
    would_recommend: Optional[bool] = None
    would_rewatch: Optional[bool] = None
    review: Optional[str] = Field(None, max_length=2000)
    completed: bool = True
    watch_percentage: float = Field(default=100.0, ge=0, le=100)


class WatchHistoryResponse(BaseModel):
    """Response schema for watch history entry"""
    id: int
    user_id: int
    movie_id: int
    watched_at: datetime
    completed: bool
    watch_percentage: float
    enjoyed: Optional[bool] = None
    rating: Optional[float] = None
    review: Optional[str] = None
    watched_with: Optional[str] = None
    mood_before: Optional[str] = None
    mood_after: Optional[str] = None
    would_recommend: Optional[bool] = None
    would_rewatch: Optional[bool] = None

    class Config:
        from_attributes = True


class WatchHistoryWithMovie(BaseModel):
    """Watch history with movie details"""
    id: int
    watched_at: datetime
    completed: bool
    rating: Optional[float] = None
    enjoyed: Optional[bool] = None
    review: Optional[str] = None
    movie: MovieListItem

    class Config:
        from_attributes = True


class WatchlistResponse(BaseModel):
    """Response for user's watchlist"""
    movies: List[MovieListItem]
    total: int


class InteractionHistoryResponse(BaseModel):
    """Paginated interaction history"""
    interactions: List[InteractionWithMovie]
    total: int
    page: int
    pages: int


class InteractionStats(BaseModel):
    """User interaction statistics"""
    total_watched: int
    total_watchlist: int
    total_passed: int
    total_favorites: int
    average_rating: Optional[float] = None
    most_common_mood: Optional[str] = None
    favorite_genres: List[str] = []
