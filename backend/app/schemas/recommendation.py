from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal
from datetime import datetime

from app.schemas.movie import MovieListItem


class CompanionPreferencesInput(BaseModel):
    """Manual companion preferences for joint recommendations"""
    preferred_genres: List[int] = Field(default_factory=list)
    disliked_genres: List[int] = Field(default_factory=list)
    year_range_min: Optional[int] = Field(None, ge=1900, le=2030)
    year_range_max: Optional[int] = Field(None, ge=1900, le=2030)
    mood_preferences: Dict[str, int] = Field(default_factory=dict)


class RecommendationRequest(BaseModel):
    """Request schema for generating recommendations"""
    mood: Optional[str] = Field(
        None,
        description="Current mood: excited, relaxed, thoughtful, adventurous, romantic, scared, nostalgic, inspired"
    )
    watching_with: Optional[Literal['alone', 'partner', 'friends', 'family']] = None
    companion_id: Optional[int] = Field(None, description="ID of linked companion account")
    companion_preferences: Optional[CompanionPreferencesInput] = Field(
        None,
        description="Manual companion preferences if not using linked account"
    )
    prefer_new_releases: Optional[bool] = Field(None, description="Prefer recent movies")
    prefer_classics: Optional[bool] = Field(None, description="Prefer classic films")
    exclude_genres: Optional[List[int]] = Field(None, description="Genres to exclude")
    count: int = Field(default=10, ge=1, le=50)


class RecommendationSource(BaseModel):
    """Information about which model contributed to a recommendation"""
    model: str  # "claude", "openai", "gemini", "collaborative", "content_based"
    score: float
    reasoning: Optional[str] = None


class RecommendationItem(BaseModel):
    """A single recommendation with movie and reasoning"""
    movie: MovieListItem
    score: float = Field(..., ge=0, le=1)
    reasoning: str
    sources: List[RecommendationSource]
    match_factors: Dict[str, float] = Field(
        default_factory=dict,
        description="Breakdown of why this matches: {genre: 0.8, mood: 0.7, ...}"
    )


class RecommendationContext(BaseModel):
    """Context information for a recommendation session"""
    mood: Optional[str] = None
    watching_with: Optional[str] = None
    companion_id: Optional[int] = None
    used_companion_preferences: bool = False
    algorithm_weights: Dict[str, float] = Field(default_factory=dict)


class RecommendationResponse(BaseModel):
    """Response for recommendation generation"""
    session_id: str
    recommendations: List[RecommendationItem]
    context: RecommendationContext
    total_candidates: int
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class RecommendationSessionResponse(BaseModel):
    """Full session details including all recommendations"""
    id: int
    session_uuid: str
    user_id: int
    mood: Optional[str] = None
    watching_with: Optional[str] = None
    companion_id: Optional[int] = None
    recommendations_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationSessionListResponse(BaseModel):
    """List of recommendation sessions"""
    sessions: List[RecommendationSessionResponse]
    total: int


class NextRecommendationsRequest(BaseModel):
    """Request for next batch of recommendations"""
    session_id: str
    count: int = Field(default=10, ge=1, le=50)


# Cold start / onboarding schemas
class OnboardingQuizQuestion(BaseModel):
    """A question for the onboarding quiz"""
    id: str
    question: str
    type: Literal['single_select', 'multi_select', 'movie_rating', 'slider']
    options: Optional[List[Dict]] = None
    movies: Optional[List[MovieListItem]] = None


class OnboardingQuizResponse(BaseModel):
    """Response containing the onboarding quiz"""
    questions: List[OnboardingQuizQuestion]


class OnboardingAnswers(BaseModel):
    """User's answers to onboarding quiz"""
    genre_selections: List[int]
    decade_preference: str
    mood_selections: List[str]
    movie_ratings: Dict[int, float] = Field(default_factory=dict)  # movie_id: rating
