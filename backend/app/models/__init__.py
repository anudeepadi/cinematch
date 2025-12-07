from app.models.user import User
from app.models.movie import Movie, Genre
from app.models.interaction import UserMovieInteraction, WatchHistory, UserPreference
from app.models.recommendation import RecommendationSession, CompanionLink, RecommendationFeedback

__all__ = [
    "User",
    "Movie",
    "Genre",
    "UserMovieInteraction",
    "WatchHistory",
    "UserPreference",
    "RecommendationSession",
    "CompanionLink",
    "RecommendationFeedback"
]
