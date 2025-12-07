"""
Companion taste merging for joint movie recommendations.
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field


@dataclass
class MergedPreferences:
    """Merged preferences from two users for joint viewing"""
    preferred_genres: List[int] = field(default_factory=list)
    excluded_genres: List[int] = field(default_factory=list)
    year_range_min: int = 1970
    year_range_max: int = 2025
    mood_scores: Dict[str, float] = field(default_factory=dict)
    viewing_context: str = "social"


class CompanionMerger:
    """
    Merges preferences of two users for joint movie recommendations.

    Algorithm:
    1. Find genre intersection (both users like)
    2. Average mood preferences with conflict resolution
    3. Expand year range to include both preferences
    4. Apply veto for strong dislikes from either party
    """

    def __init__(self):
        self.veto_threshold = 2  # If either user rates below this, exclude

    def merge_preferences(
        self,
        user_genres: List[int],
        user_year_min: int,
        user_year_max: int,
        user_moods: Dict[str, int],
        companion_genres: List[int],
        companion_year_min: int,
        companion_year_max: int,
        companion_moods: Dict[str, int],
        user_disliked_genres: List[int] = None,
        companion_disliked_genres: List[int] = None
    ) -> MergedPreferences:
        """Merge two users' preferences for joint recommendations"""

        # Merge genres: prefer intersection, fall back to union
        merged_genres = self._merge_genres(
            set(user_genres or []),
            set(companion_genres or [])
        )

        # Merge excluded genres: union of dislikes
        excluded = set(user_disliked_genres or [])
        excluded.update(companion_disliked_genres or [])

        # Merge year range: union (widest acceptable range)
        merged_year_min = min(user_year_min, companion_year_min)
        merged_year_max = max(user_year_max, companion_year_max)

        # Merge mood scores with veto
        merged_moods = self._merge_moods(user_moods, companion_moods)

        return MergedPreferences(
            preferred_genres=list(merged_genres),
            excluded_genres=list(excluded),
            year_range_min=merged_year_min,
            year_range_max=merged_year_max,
            mood_scores=merged_moods,
            viewing_context="social"
        )

    def _merge_genres(
        self,
        user_genres: Set[int],
        companion_genres: Set[int]
    ) -> List[int]:
        """
        Merge genre preferences.

        Priority:
        1. Genres both users like (intersection)
        2. If no intersection, use union of top genres from each
        """
        intersection = user_genres & companion_genres

        if intersection:
            return list(intersection)

        # No intersection - combine top genres from each
        # Take up to 3 from each user
        user_top = list(user_genres)[:3]
        companion_top = list(companion_genres)[:3]

        combined = set(user_top + companion_top)
        return list(combined)

    def _merge_moods(
        self,
        user_moods: Dict[str, int],
        companion_moods: Dict[str, int]
    ) -> Dict[str, float]:
        """
        Merge mood preferences with veto power for strong dislikes.

        - Average scores for moods both users rate 2+
        - Veto (low score) if either user rates below 2
        """
        all_moods = set(user_moods.keys()) | set(companion_moods.keys())
        merged = {}

        for mood in all_moods:
            user_score = user_moods.get(mood, 3)  # Default neutral
            companion_score = companion_moods.get(mood, 3)

            # Veto check: if either person dislikes, reduce score
            if user_score < self.veto_threshold or companion_score < self.veto_threshold:
                merged[mood] = min(user_score, companion_score) / 5.0
            else:
                # Average the scores
                merged[mood] = (user_score + companion_score) / 10.0

        return merged

    def calculate_compatibility_score(
        self,
        user_genres: List[int],
        user_moods: Dict[str, int],
        companion_genres: List[int],
        companion_moods: Dict[str, int]
    ) -> float:
        """
        Calculate taste compatibility between two users.

        Returns:
            Score between 0 (incompatible) and 1 (highly compatible)
        """
        # Genre compatibility
        user_set = set(user_genres or [])
        companion_set = set(companion_genres or [])

        if user_set and companion_set:
            genre_overlap = len(user_set & companion_set) / len(user_set | companion_set)
        else:
            genre_overlap = 0.5  # Neutral if no preferences

        # Mood compatibility
        all_moods = set(user_moods.keys()) | set(companion_moods.keys())
        if all_moods:
            mood_diffs = []
            for mood in all_moods:
                u = user_moods.get(mood, 3)
                c = companion_moods.get(mood, 3)
                diff = abs(u - c) / 5.0  # Normalize to 0-1
                mood_diffs.append(1 - diff)
            mood_compat = sum(mood_diffs) / len(mood_diffs)
        else:
            mood_compat = 0.5

        # Weighted average
        return genre_overlap * 0.6 + mood_compat * 0.4

    def get_compromise_reasoning(
        self,
        merged: MergedPreferences,
        movie_genres: List[int],
        movie_mood_scores: Dict[str, float]
    ) -> str:
        """Generate reasoning for why a movie works for both viewers"""

        reasons = []

        # Check genre match
        movie_genre_set = set(movie_genres)
        merged_genre_set = set(merged.preferred_genres)

        matching_genres = movie_genre_set & merged_genre_set
        if matching_genres:
            reasons.append("matches genres you both enjoy")

        # Check mood alignment
        if movie_mood_scores and merged.mood_scores:
            avg_mood_match = sum(
                movie_mood_scores.get(m, 0) * merged.mood_scores.get(m, 0.5)
                for m in merged.mood_scores
            ) / len(merged.mood_scores)

            if avg_mood_match > 0.6:
                reasons.append("fits both of your moods")

        # Check no vetoes
        excluded_match = movie_genre_set & set(merged.excluded_genres)
        if not excluded_match:
            reasons.append("avoids genres either of you dislike")

        if reasons:
            return "Great for watching together: " + ", ".join(reasons) + "."
        else:
            return "A balanced choice that should work for both of you."
