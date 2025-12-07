from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class InteractionType(str, enum.Enum):
    WATCH = "watch"  # User wants to watch
    PASS = "pass"  # User passed on this movie
    WATCHED = "watched"  # User has already watched
    FAVORITE = "favorite"  # User favorited
    RATING = "rating"  # User rated the movie


class UserMovieInteraction(Base):
    """Tracks all user interactions with movies (pass/watch/rate)"""
    __tablename__ = "user_movie_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False, index=True)

    interaction_type = Column(String(50), nullable=False, index=True)
    rating = Column(Float, nullable=True)  # 1-10 scale

    # Context at time of interaction
    mood_at_interaction = Column(String(50), nullable=True)
    watching_with = Column(String(50), nullable=True)  # alone, partner, friends, family
    context_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="interactions")
    movie = relationship("Movie", back_populates="interactions")

    def __repr__(self):
        return f"<Interaction user={self.user_id} movie={self.movie_id} type={self.interaction_type}>"


class WatchHistory(Base):
    """Detailed watch history with viewing context"""
    __tablename__ = "watch_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False, index=True)

    # Watch details
    watched_at = Column(DateTime, default=datetime.utcnow)
    completed = Column(Boolean, default=True)
    watch_percentage = Column(Float, default=100.0)

    # Post-watch feedback
    enjoyed = Column(Boolean, nullable=True)
    rating = Column(Float, nullable=True)
    review = Column(Text, nullable=True)

    # Viewing context
    watched_with = Column(String(50), nullable=True)  # alone, partner, friends, family
    mood_before = Column(String(50), nullable=True)
    mood_after = Column(String(50), nullable=True)
    would_recommend = Column(Boolean, nullable=True)
    would_rewatch = Column(Boolean, nullable=True)

    # Relationships
    user = relationship("User", back_populates="watch_history")

    def __repr__(self):
        return f"<WatchHistory user={self.user_id} movie={self.movie_id}>"


class UserPreference(Base):
    """Detailed user preferences for recommendations"""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Genre preferences (learned from interactions)
    genre_weights = Column(JSON, default=dict)  # {genre_id: weight}

    # Temporal preferences
    preferred_decades = Column(JSON, default=list)  # [1990, 2000, 2010, 2020]
    new_releases_interest = Column(Float, default=0.5)  # 0-1 scale
    classics_interest = Column(Float, default=0.5)  # 0-1 scale

    # Content preferences (learned)
    actor_preferences = Column(JSON, default=dict)  # {actor_id: score}
    director_preferences = Column(JSON, default=dict)  # {director_id: score}
    keyword_preferences = Column(JSON, default=dict)  # {keyword: score}

    # Viewing patterns
    avg_rating = Column(Float, nullable=True)
    total_watched = Column(Integer, default=0)
    total_passed = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)

    # Computed embeddings for similarity
    preference_embedding = Column(JSON, nullable=True)

    # Last updated
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreference user={self.user_id}>"
