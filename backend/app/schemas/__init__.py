from app.schemas.auth import (
    UserCreate,
    UserLogin,
    Token,
    TokenPayload
)
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    UserPreferencesUpdate,
    UserPreferencesResponse,
    OnboardingPreferences
)
from app.schemas.movie import (
    MovieResponse,
    MovieListResponse,
    MovieSearchQuery,
    GenreResponse
)
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationItem,
    RecommendationResponse,
    RecommendationSessionResponse,
    CompanionPreferencesInput
)
from app.schemas.interaction import (
    InteractionCreate,
    InteractionResponse,
    WatchHistoryCreate,
    WatchHistoryResponse,
    WatchlistResponse
)
from app.schemas.companion import (
    CompanionLinkRequest,
    CompanionLinkResponse,
    CompanionResponse
)

__all__ = [
    # Auth
    "UserCreate", "UserLogin", "Token", "TokenPayload",
    # User
    "UserResponse", "UserUpdate", "UserPreferencesUpdate",
    "UserPreferencesResponse", "OnboardingPreferences",
    # Movie
    "MovieResponse", "MovieListResponse", "MovieSearchQuery", "GenreResponse",
    # Recommendation
    "RecommendationRequest", "RecommendationItem", "RecommendationResponse",
    "RecommendationSessionResponse", "CompanionPreferencesInput",
    # Interaction
    "InteractionCreate", "InteractionResponse", "WatchHistoryCreate",
    "WatchHistoryResponse", "WatchlistResponse",
    # Companion
    "CompanionLinkRequest", "CompanionLinkResponse", "CompanionResponse"
]
