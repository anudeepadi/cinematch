from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.database import Base


class LinkStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class RecommendationSession(Base):
    """Stores a recommendation session with context and results"""
    __tablename__ = "recommendation_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Context for this session
    mood = Column(String(50), nullable=True)
    watching_with = Column(String(50), nullable=True)  # alone, partner, friends, family
    companion_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    companion_preferences = Column(JSON, nullable=True)  # Manual companion prefs if not linked

    # Preference overrides for this session
    prefer_new_releases = Column(Integer, default=0)  # 0=no preference, 1=yes, -1=no
    prefer_classics = Column(Integer, default=0)
    exclude_genres = Column(JSON, default=list)

    # Algorithm configuration used
    algorithm_weights = Column(JSON, default=dict)  # {collaborative: 0.3, content: 0.3, ...}

    # Results
    recommendations = Column(JSON, default=list)  # List of {movie_id, score, reasoning, sources}
    total_candidates = Column(Integer, default=0)

    # Model contributions (for analysis)
    claude_recommendations = Column(JSON, nullable=True)
    openai_recommendations = Column(JSON, nullable=True)
    gemini_recommendations = Column(JSON, nullable=True)
    collaborative_recommendations = Column(JSON, nullable=True)
    content_based_recommendations = Column(JSON, nullable=True)

    # Merged preferences (when watching with companion)
    merged_preferences = Column(JSON, nullable=True)

    # Session tracking
    recommendations_shown = Column(Integer, default=0)
    current_index = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="recommendation_sessions", foreign_keys=[user_id])

    def __repr__(self):
        return f"<RecommendationSession {self.session_uuid} user={self.user_id}>"


class CompanionLink(Base):
    """Links two users for joint movie recommendations"""
    __tablename__ = "companion_links"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    companion_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    status = Column(String(20), default="pending", index=True)  # pending, accepted, rejected
    nickname = Column(String(100), nullable=True)  # User's nickname for this companion

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="sent_companion_requests")
    companion = relationship("User", foreign_keys=[companion_id], backref="received_companion_requests")

    def __repr__(self):
        return f"<CompanionLink user={self.user_id} companion={self.companion_id} status={self.status}>"


class RecommendationFeedback(Base):
    """Stores feedback on individual recommendations for learning"""
    __tablename__ = "recommendation_feedback"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("recommendation_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False, index=True)

    # User action
    action = Column(String(20), nullable=False)  # watch, pass, skip
    time_spent_viewing = Column(Integer, nullable=True)  # seconds spent viewing this card

    # Which models contributed to this recommendation
    contributing_models = Column(JSON, default=list)
    final_score = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<RecommendationFeedback session={self.session_id} movie={self.movie_id} action={self.action}>"
