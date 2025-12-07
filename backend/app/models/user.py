from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # User preferences for recommendations
    preferred_genres = Column(JSON, default=list)  # List of genre IDs
    year_range_min = Column(Integer, default=1970)
    year_range_max = Column(Integer, default=2025)
    preferred_languages = Column(JSON, default=lambda: ["en"])

    # Mood preferences (1-5 scale)
    mood_action = Column(Integer, default=3)
    mood_comedy = Column(Integer, default=3)
    mood_drama = Column(Integer, default=3)
    mood_horror = Column(Integer, default=3)
    mood_romance = Column(Integer, default=3)
    mood_scifi = Column(Integer, default=3)
    mood_thriller = Column(Integer, default=3)
    mood_documentary = Column(Integer, default=3)

    # Social viewing preferences
    watch_alone_preference = Column(Integer, default=3)  # 1-5: alone to social

    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_onboarded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    interactions = relationship("UserMovieInteraction", back_populates="user", lazy="dynamic")
    watch_history = relationship("WatchHistory", back_populates="user", lazy="dynamic")
    preferences = relationship("UserPreference", back_populates="user", uselist=False)
    recommendation_sessions = relationship(
        "RecommendationSession",
        back_populates="user",
        lazy="dynamic",
        foreign_keys="[RecommendationSession.user_id]"
    )

    def __repr__(self):
        return f"<User {self.username}>"
