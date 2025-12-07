"""
Embedding generator for movie content.

Uses sentence-transformers to generate embeddings for movies based on:
- Title
- Overview
- Genres
- Keywords
- Directors
- Top cast members

These embeddings are used for content-based recommendation similarity.
"""

from typing import List, Optional
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.movie import Movie


class EmbeddingGenerator:
    """Generate and manage movie content embeddings"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        """Lazy load the sentence transformer model"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for embeddings. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    def build_movie_text(self, movie: Movie) -> str:
        """Build text representation of a movie for embedding"""
        parts = []

        # Title (important, add twice for emphasis)
        if movie.title:
            parts.append(movie.title)
            parts.append(movie.title)

        # Overview
        if movie.overview:
            parts.append(movie.overview)

        # Genres
        if movie.genres:
            genre_names = [g.name for g in movie.genres]
            parts.append(" ".join(genre_names))

        # Keywords
        if movie.keywords:
            parts.append(" ".join(movie.keywords[:20]))  # Limit keywords

        # Directors
        if movie.directors:
            director_names = [d.get("name", "") for d in movie.directors if isinstance(d, dict)]
            if director_names:
                parts.append("Directed by " + ", ".join(director_names))

        # Top cast
        if movie.cast:
            cast_names = [c.get("name", "") for c in movie.cast[:5] if isinstance(c, dict)]
            if cast_names:
                parts.append("Starring " + ", ".join(cast_names))

        return " ".join(parts)

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a text string"""
        embedding = self.model.encode(text)
        return embedding.tolist()

    def generate_movie_embedding(self, movie: Movie) -> List[float]:
        """Generate embedding for a movie"""
        text = self.build_movie_text(movie)
        return self.generate_embedding(text)

    async def generate_embeddings_for_movies(
        self,
        db: AsyncSession,
        batch_size: int = 100,
        force_regenerate: bool = False,
        progress_callback=None
    ) -> int:
        """Generate embeddings for all movies without embeddings"""
        # Query movies needing embeddings
        if force_regenerate:
            stmt = select(Movie).options(selectinload(Movie.genres))
        else:
            stmt = (
                select(Movie)
                .options(selectinload(Movie.genres))
                .where(Movie.content_embedding.is_(None))
            )

        result = await db.execute(stmt)
        movies = result.scalars().all()

        total = len(movies)
        count = 0

        # Process in batches
        for i in range(0, total, batch_size):
            batch = movies[i:i + batch_size]

            # Generate embeddings
            texts = [self.build_movie_text(m) for m in batch]
            embeddings = self.model.encode(texts)

            # Update movies
            for movie, embedding in zip(batch, embeddings):
                movie.content_embedding = embedding.tolist()
                count += 1

            await db.commit()

            if progress_callback:
                progress_callback(count, total)

        return count

    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """Compute cosine similarity between two embeddings"""
        e1 = np.array(embedding1)
        e2 = np.array(embedding2)

        dot_product = np.dot(e1, e2)
        norm1 = np.linalg.norm(e1)
        norm2 = np.linalg.norm(e2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def find_similar_movies(
        self,
        target_embedding: List[float],
        movie_embeddings: List[tuple],  # List of (movie_id, embedding)
        top_k: int = 10
    ) -> List[tuple]:
        """Find most similar movies to target embedding"""
        similarities = []

        for movie_id, embedding in movie_embeddings:
            if embedding:
                sim = self.compute_similarity(target_embedding, embedding)
                similarities.append((movie_id, sim))

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def compute_user_preference_embedding(
        self,
        liked_embeddings: List[List[float]],
        disliked_embeddings: List[List[float]] = None,
        like_weight: float = 1.0,
        dislike_weight: float = 0.5
    ) -> List[float]:
        """
        Compute a user preference embedding from their liked/disliked movies.

        Liked movies contribute positively, disliked movies negatively.
        """
        if not liked_embeddings:
            return None

        # Compute weighted average of liked embeddings
        liked_array = np.array(liked_embeddings)
        preference = np.mean(liked_array, axis=0) * like_weight

        # Subtract disliked embeddings
        if disliked_embeddings:
            disliked_array = np.array(disliked_embeddings)
            dislike_avg = np.mean(disliked_array, axis=0)
            preference = preference - (dislike_avg * dislike_weight)

        # Normalize
        norm = np.linalg.norm(preference)
        if norm > 0:
            preference = preference / norm

        return preference.tolist()


async def generate_all_embeddings(
    db: AsyncSession,
    force_regenerate: bool = False
):
    """Utility function to generate embeddings for all movies"""
    generator = EmbeddingGenerator()

    def progress(current, total):
        percent = (current / total) * 100
        print(f"\r  Progress: {current}/{total} ({percent:.1f}%)", end="", flush=True)

    print("Generating movie embeddings...")
    count = await generator.generate_embeddings_for_movies(
        db,
        force_regenerate=force_regenerate,
        progress_callback=progress
    )
    print(f"\n  Generated embeddings for {count} movies.")
    return count
