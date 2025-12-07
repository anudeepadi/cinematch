"""
Base recommender interface for the multi-model ensemble system.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class RecommendationResult:
    """A single recommendation from a recommender"""
    movie_id: int
    tmdb_id: int
    title: str
    score: float  # 0-1 normalized score
    reasoning: str
    source: str  # Which recommender generated this
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserPreferences:
    """User preferences for recommendation"""
    user_id: int
    preferred_genres: List[int] = field(default_factory=list)
    disliked_genres: List[int] = field(default_factory=list)
    year_range_min: int = 1970
    year_range_max: int = 2025
    mood_scores: Dict[str, int] = field(default_factory=dict)
    genre_weights: Dict[int, float] = field(default_factory=dict)
    liked_movie_ids: List[int] = field(default_factory=list)
    disliked_movie_ids: List[int] = field(default_factory=list)
    watched_movie_ids: List[int] = field(default_factory=list)
    history_count: int = 0


@dataclass
class RecommendationContext:
    """Context for a recommendation request"""
    mood: Optional[str] = None
    watching_with: Optional[str] = None  # alone, partner, friends, family
    prefer_new_releases: bool = False
    prefer_classics: bool = False
    exclude_genres: List[int] = field(default_factory=list)
    exclude_movie_ids: List[int] = field(default_factory=list)


class BaseRecommender(ABC):
    """Abstract base class for all recommenders"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name identifier for this recommender"""
        pass

    @abstractmethod
    async def recommend(
        self,
        user_preferences: UserPreferences,
        context: RecommendationContext,
        count: int = 10
    ) -> List[RecommendationResult]:
        """
        Generate recommendations based on user preferences and context.

        Args:
            user_preferences: User's preferences and history
            context: Current recommendation context
            count: Number of recommendations to return

        Returns:
            List of RecommendationResult objects
        """
        pass

    def get_weight(self, history_count: int) -> float:
        """
        Get the weight for this recommender in the ensemble.

        Recommenders can override this to adjust their weight based on
        how much user history is available.

        Args:
            history_count: Number of movies in user's history

        Returns:
            Weight between 0 and 1
        """
        return 0.2  # Default weight

    async def is_available(self) -> bool:
        """Check if this recommender is available (API keys, etc.)"""
        return True
