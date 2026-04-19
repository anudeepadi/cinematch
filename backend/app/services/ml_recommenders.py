"""
Machine Learning Recommenders: RandomForest and KNN-based collaborative filtering.

These recommenders learn from user interaction patterns to provide personalized
movie recommendations.
"""

import os
import math
from pathlib import Path
from typing import List, Dict, Optional, Set
from collections import defaultdict

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import NearestNeighbors
import joblib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.movie import Movie, Genre
from app.models.interaction import UserMovieInteraction
from app.services.recommenders.base import (
    BaseRecommender,
    UserPreferences,
    RecommendationContext,
    RecommendationResult,
)


# Directory for persisting trained models
MODELS_DIR = Path(__file__).parent.parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)


class RandomForestRecommender(BaseRecommender):
    """
    RandomForest-based recommender that learns user preferences from interactions.
    
    Features used for classification:
    1. genre_match_score - Jaccard similarity between user's preferred genres and movie genres
    2. mood_compatibility - Match between movie mood_scores and user mood preferences
    3. year_preference_match - Score based on distance from user's year range
    4. popularity_normalized - movie.popularity / 500 (capped at 1.0)
    5. rating_normalized - movie.vote_average / 10
    6. user_watch_frequency - Log-normalized user engagement level
    7. genre_popularity - How popular genre is across all users
    
    Model Configuration:
    - RandomForestClassifier(n_estimators=100, max_depth=10, class_weight='balanced')
    - Train on interactions: watch/favorite=1, pass=0
    - Minimum 10 interactions required for training
    - Models persisted to models/rf_user_{user_id}.joblib
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._genre_popularity: Dict[int, float] = {}
        self._all_genres: List[Genre] = []

    @property
    def name(self) -> str:
        return "random_forest"

    async def is_available(self) -> bool:
        """Always available - no external API needed"""
        return True

    def get_weight(self, history_count: int) -> float:
        """Weight increases with more user history"""
        if history_count < 10:
            return 0.0  # Not enough data
        elif history_count < 30:
            return 0.10
        elif history_count < 50:
            return 0.13
        return 0.15

    async def recommend(
        self,
        user_preferences: UserPreferences,
        context: RecommendationContext,
        count: int = 10,
    ) -> List[RecommendationResult]:
        """Generate recommendations using RandomForest model"""

        # Check minimum interactions
        if user_preferences.history_count < 10:
            return []

        # Load or train model
        model = await self._get_or_train_model(user_preferences)
        if model is None:
            return []

        # Load genre data
        await self._load_genre_data()

        # Get candidate movies
        candidates = await self._get_candidate_movies(user_preferences, context, count * 5)
        if not candidates:
            return []

        # Score candidates
        results = []
        for movie in candidates:
            features = self._extract_features(movie, user_preferences)
            # Get probability of positive class (watch/favorite)
            try:
                proba = model.predict_proba([features])[0]
                score = proba[1] if len(proba) > 1 else proba[0]
            except Exception:
                score = 0.5

            results.append(
                RecommendationResult(
                    movie_id=movie.id,
                    tmdb_id=movie.tmdb_id,
                    title=movie.title,
                    score=float(score),
                    reasoning=self._generate_reasoning(movie, features, score),
                    source=self.name,
                    metadata={
                        "genre_match": features[0],
                        "mood_compat": features[1],
                        "year_match": features[2],
                        "popularity": features[3],
                        "rating": features[4],
                    },
                )
            )

        # Sort by score and return top count
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:count]

    async def _get_or_train_model(
        self, user_preferences: UserPreferences
    ) -> Optional[RandomForestClassifier]:
        """Load existing model or train a new one"""
        model_path = MODELS_DIR / f"rf_user_{user_preferences.user_id}.joblib"

        # Try to load existing model
        if model_path.exists():
            try:
                return joblib.load(model_path)
            except Exception:
                pass  # Re-train if load fails

        # Train new model
        return await self._train_model(user_preferences, model_path)

    async def _train_model(
        self, user_preferences: UserPreferences, model_path: Path
    ) -> Optional[RandomForestClassifier]:
        """Train a new RandomForest model for the user"""

        # Get user's interactions
        result = await self.db.execute(
            select(UserMovieInteraction)
            .where(UserMovieInteraction.user_id == user_preferences.user_id)
            .options(selectinload(UserMovieInteraction.movie))
        )
        interactions = result.scalars().all()

        if len(interactions) < 10:
            return None

        # Load genre data for feature extraction
        await self._load_genre_data()

        # Build training data
        X = []
        y = []

        for interaction in interactions:
            movie = interaction.movie
            if movie is None:
                continue

            features = self._extract_features(movie, user_preferences)
            X.append(features)

            # Label: 1 for positive interactions, 0 for negative
            if interaction.interaction_type in ("watch", "favorite"):
                y.append(1)
            else:
                y.append(0)

        if len(X) < 10 or sum(y) < 2 or len(y) - sum(y) < 2:
            return None  # Need minimum samples of each class

        X = np.array(X)
        y = np.array(y)

        # Train model
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X, y)

        # Save model
        try:
            joblib.dump(model, model_path)
        except Exception:
            pass  # Non-critical if save fails

        return model

    async def _load_genre_data(self):
        """Load genre popularity data"""
        if self._all_genres:
            return

        # Get all genres
        result = await self.db.execute(select(Genre))
        self._all_genres = list(result.scalars().all())

        # Calculate genre popularity
        for genre in self._all_genres:
            count_result = await self.db.execute(
                select(func.count())
                .select_from(UserMovieInteraction)
                .join(Movie)
                .where(Movie.genres.any(Genre.id == genre.id))
            )
            count = count_result.scalar() or 0
            self._genre_popularity[genre.id] = count

        # Normalize genre popularity
        max_pop = max(self._genre_popularity.values()) if self._genre_popularity else 1
        for genre_id in self._genre_popularity:
            self._genre_popularity[genre_id] /= max_pop

    async def _get_candidate_movies(
        self,
        user_preferences: UserPreferences,
        context: RecommendationContext,
        count: int,
    ) -> List[Movie]:
        """Get candidate movies for recommendation"""

        query = (
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(Movie.id.notin_(context.exclude_movie_ids))
        )

        # Apply year filter
        if user_preferences.year_range_min:
            query = query.where(Movie.release_year >= user_preferences.year_range_min)
        if user_preferences.year_range_max:
            query = query.where(Movie.release_year <= user_preferences.year_range_max)

        # Exclude genres
        if context.exclude_genres:
            for genre_id in context.exclude_genres:
                query = query.where(~Movie.genres.any(Genre.id == genre_id))

        # Order by popularity for diverse candidates
        query = query.order_by(Movie.popularity.desc()).limit(count)

        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    def _extract_features(
        self, movie: Movie, user_preferences: UserPreferences
    ) -> List[float]:
        """Extract 7 features for the model"""

        # 1. Genre match score (Jaccard similarity)
        movie_genre_ids = {g.id for g in movie.genres} if movie.genres else set()
        user_genre_ids = set(user_preferences.preferred_genres)
        if movie_genre_ids and user_genre_ids:
            genre_match = len(movie_genre_ids & user_genre_ids) / len(
                movie_genre_ids | user_genre_ids
            )
        else:
            genre_match = 0.0

        # 2. Mood compatibility
        movie_moods = movie.mood_scores or {}
        user_moods = user_preferences.mood_scores or {}
        if movie_moods and user_moods:
            mood_compat = 0.0
            count = 0
            for mood, user_score in user_moods.items():
                if mood in movie_moods:
                    # Normalize user score (1-5) to 0-1
                    user_norm = user_score / 5.0
                    movie_norm = movie_moods[mood]
                    mood_compat += 1 - abs(user_norm - movie_norm)
                    count += 1
            mood_compat = mood_compat / count if count > 0 else 0.5
        else:
            mood_compat = 0.5

        # 3. Year preference match
        release_year = movie.release_year or 2000
        year_min = user_preferences.year_range_min or 1970
        year_max = user_preferences.year_range_max or 2025
        if year_min <= release_year <= year_max:
            year_match = 1.0
        else:
            distance = min(abs(release_year - year_min), abs(release_year - year_max))
            year_match = max(0, 1 - distance / 50)

        # 4. Popularity normalized (capped at 1.0)
        popularity = min((movie.popularity or 0) / 500, 1.0)

        # 5. Rating normalized
        rating = (movie.vote_average or 5.0) / 10.0

        # 6. User watch frequency (log normalized)
        watch_freq = math.log(user_preferences.history_count + 1) / 5.0
        watch_freq = min(watch_freq, 1.0)

        # 7. Genre popularity (average of movie's genres)
        if movie_genre_ids:
            genre_pop = sum(
                self._genre_popularity.get(gid, 0.5) for gid in movie_genre_ids
            ) / len(movie_genre_ids)
        else:
            genre_pop = 0.5

        return [
            genre_match,
            mood_compat,
            year_match,
            popularity,
            rating,
            watch_freq,
            genre_pop,
        ]

    def _generate_reasoning(
        self, movie: Movie, features: List[float], score: float
    ) -> str:
        """Generate human-readable reasoning"""
        reasons = []

        if features[0] > 0.5:
            reasons.append("matches your genre preferences")
        if features[1] > 0.6:
            reasons.append("fits your mood")
        if features[4] > 0.7:
            reasons.append(f"highly rated ({movie.vote_average:.1f}/10)")
        if features[3] > 0.5:
            reasons.append("popular choice")

        if not reasons:
            reasons.append("predicted to match your taste")

        return f"Based on your viewing history: {', '.join(reasons)}"


class KNNRecommender(BaseRecommender):
    """
    K-Nearest Neighbors collaborative filtering recommender.
    
    Approach:
    - Build sparse user-movie interaction matrix (scipy.sparse.csr_matrix)
    - NearestNeighbors(n_neighbors=11, metric='cosine', algorithm='brute')
    - Find K=10 similar users, aggregate their liked movies
    - Score: sum(similarity * rating) for each candidate movie
    
    Cold Start Handling:
    - If < 3 interactions: return popular movies with vote_average >= 7.0
    
    Interaction Values:
    - favorite: 0.8
    - watch: 0.8
    - watched: 0.6
    - pass: 0.2
    """

    # Interaction type weights
    INTERACTION_WEIGHTS = {
        "favorite": 0.8,
        "watch": 0.8,
        "watched": 0.6,
        "pass": 0.2,
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self._user_movie_matrix: Optional[csr_matrix] = None
        self._user_id_map: Dict[int, int] = {}  # user_id -> matrix row index
        self._movie_id_map: Dict[int, int] = {}  # movie_id -> matrix col index
        self._reverse_movie_map: Dict[int, int] = {}  # matrix col -> movie_id
        self._knn_model: Optional[NearestNeighbors] = None

    @property
    def name(self) -> str:
        return "knn"

    async def is_available(self) -> bool:
        """Always available - no external API needed"""
        return True

    def get_weight(self, history_count: int) -> float:
        """Weight increases with more user history"""
        if history_count < 3:
            return 0.0  # Cold start
        elif history_count < 10:
            return 0.05
        elif history_count < 30:
            return 0.08
        return 0.10

    async def recommend(
        self,
        user_preferences: UserPreferences,
        context: RecommendationContext,
        count: int = 10,
    ) -> List[RecommendationResult]:
        """Generate recommendations using KNN collaborative filtering"""

        # Cold start handling
        if user_preferences.history_count < 3:
            return await self._cold_start_recommendations(context, count)

        # Build or use cached matrix
        await self._build_matrix()

        if self._user_movie_matrix is None or self._knn_model is None:
            return await self._cold_start_recommendations(context, count)

        # Check if user is in matrix
        if user_preferences.user_id not in self._user_id_map:
            return await self._cold_start_recommendations(context, count)

        user_idx = self._user_id_map[user_preferences.user_id]

        # Find similar users
        try:
            user_vector = self._user_movie_matrix[user_idx].toarray().reshape(1, -1)
            distances, indices = self._knn_model.kneighbors(user_vector)
        except Exception:
            return await self._cold_start_recommendations(context, count)

        # Skip first result (self) and aggregate neighbor preferences
        movie_scores: Dict[int, float] = defaultdict(float)
        
        for i, neighbor_idx in enumerate(indices[0][1:]):  # Skip self
            similarity = 1 - distances[0][i + 1]  # Convert distance to similarity
            if similarity <= 0:
                continue

            # Get neighbor's interactions
            neighbor_vector = self._user_movie_matrix[neighbor_idx].toarray().flatten()
            for movie_col, rating in enumerate(neighbor_vector):
                if rating > 0:
                    movie_id = self._reverse_movie_map.get(movie_col)
                    if movie_id and movie_id not in context.exclude_movie_ids:
                        movie_scores[movie_id] += similarity * rating

        if not movie_scores:
            return await self._cold_start_recommendations(context, count)

        # Get top scored movies
        sorted_movies = sorted(movie_scores.items(), key=lambda x: x[1], reverse=True)
        top_movie_ids = [mid for mid, _ in sorted_movies[: count * 2]]

        # Load movie details
        result = await self.db.execute(
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(Movie.id.in_(top_movie_ids))
        )
        movies = {m.id: m for m in result.scalars().unique().all()}

        # Build results
        results = []
        for movie_id, agg_score in sorted_movies[:count]:
            movie = movies.get(movie_id)
            if not movie:
                continue

            # Normalize score
            max_score = sorted_movies[0][1] if sorted_movies else 1
            normalized_score = min(agg_score / max_score, 1.0) if max_score > 0 else 0.5

            results.append(
                RecommendationResult(
                    movie_id=movie.id,
                    tmdb_id=movie.tmdb_id,
                    title=movie.title,
                    score=normalized_score,
                    reasoning="Recommended based on similar users' preferences",
                    source=self.name,
                    metadata={
                        "aggregate_score": agg_score,
                        "similar_users_liked": True,
                    },
                )
            )

        return results[:count]

    async def _build_matrix(self):
        """Build or rebuild the user-movie interaction matrix"""
        if self._user_movie_matrix is not None:
            return  # Use cached matrix

        # Get all interactions
        result = await self.db.execute(select(UserMovieInteraction))
        interactions = result.scalars().all()

        if not interactions:
            return

        # Build ID mappings
        user_ids: Set[int] = set()
        movie_ids: Set[int] = set()

        for interaction in interactions:
            user_ids.add(interaction.user_id)
            movie_ids.add(interaction.movie_id)

        self._user_id_map = {uid: i for i, uid in enumerate(sorted(user_ids))}
        self._movie_id_map = {mid: i for i, mid in enumerate(sorted(movie_ids))}
        self._reverse_movie_map = {i: mid for mid, i in self._movie_id_map.items()}

        # Build sparse matrix
        rows = []
        cols = []
        data = []

        for interaction in interactions:
            row = self._user_id_map[interaction.user_id]
            col = self._movie_id_map[interaction.movie_id]
            weight = self.INTERACTION_WEIGHTS.get(interaction.interaction_type, 0.5)

            rows.append(row)
            cols.append(col)
            data.append(weight)

        n_users = len(self._user_id_map)
        n_movies = len(self._movie_id_map)

        self._user_movie_matrix = csr_matrix(
            (data, (rows, cols)), shape=(n_users, n_movies)
        )

        # Build KNN model
        self._knn_model = NearestNeighbors(
            n_neighbors=min(11, n_users),  # 10 neighbors + self
            metric="cosine",
            algorithm="brute",
        )
        self._knn_model.fit(self._user_movie_matrix)

    async def _cold_start_recommendations(
        self, context: RecommendationContext, count: int
    ) -> List[RecommendationResult]:
        """Return popular movies for cold start users"""

        query = (
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(
                Movie.id.notin_(context.exclude_movie_ids),
                Movie.vote_average >= 7.0,
            )
            .order_by(Movie.popularity.desc())
            .limit(count)
        )

        result = await self.db.execute(query)
        movies = result.scalars().unique().all()

        return [
            RecommendationResult(
                movie_id=movie.id,
                tmdb_id=movie.tmdb_id,
                title=movie.title,
                score=min(movie.popularity / 500, 1.0) if movie.popularity else 0.5,
                reasoning=f"Popular and highly rated ({movie.vote_average:.1f}/10)",
                source=self.name,
                metadata={"cold_start": True, "vote_average": movie.vote_average},
            )
            for movie in movies
        ]

    def invalidate_cache(self):
        """Invalidate cached matrix (call when interactions change significantly)"""
        self._user_movie_matrix = None
        self._knn_model = None
