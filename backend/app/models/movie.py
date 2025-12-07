from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Table, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

# Association table for movie-genre many-to-many relationship
movie_genres = Table(
    'movie_genres',
    Base.metadata,
    Column('movie_id', Integer, ForeignKey('movies.id'), primary_key=True),
    Column('genre_id', Integer, ForeignKey('genres.id'), primary_key=True)
)


class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, unique=True, index=True)
    name = Column(String(100), nullable=False)

    movies = relationship("Movie", secondary=movie_genres, back_populates="genres", lazy="selectin")

    def __repr__(self):
        return f"<Genre {self.name}>"


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, unique=True, index=True, nullable=False)
    imdb_id = Column(String(20), unique=True, nullable=True)

    # Basic info
    title = Column(String(500), nullable=False, index=True)
    original_title = Column(String(500), nullable=True)
    tagline = Column(String(500), nullable=True)
    overview = Column(Text, nullable=True)

    # Release info
    release_date = Column(DateTime, nullable=True)
    release_year = Column(Integer, nullable=True, index=True)
    runtime = Column(Integer, nullable=True)  # in minutes

    # Ratings and popularity
    vote_average = Column(Float, default=0.0)
    vote_count = Column(Integer, default=0)
    popularity = Column(Float, default=0.0)

    # Media
    poster_path = Column(String(500), nullable=True)
    backdrop_path = Column(String(500), nullable=True)

    # Additional metadata
    original_language = Column(String(10), default="en")
    spoken_languages = Column(JSON, default=list)
    production_countries = Column(JSON, default=list)

    # Cast and crew (stored as JSON for flexibility)
    cast = Column(JSON, default=list)  # List of {id, name, character, profile_path}
    directors = Column(JSON, default=list)  # List of {id, name}

    # Keywords and themes for content-based filtering
    keywords = Column(JSON, default=list)

    # Mood indicators (computed from analysis)
    mood_scores = Column(JSON, default=dict)  # {action: 0.8, comedy: 0.2, ...}

    # Embedding for similarity (stored as JSON array)
    content_embedding = Column(JSON, nullable=True)

    # Status
    is_adult = Column(Integer, default=0)
    status = Column(String(50), default="Released")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    genres = relationship("Genre", secondary=movie_genres, back_populates="movies", lazy="selectin")
    interactions = relationship("UserMovieInteraction", back_populates="movie", lazy="dynamic")

    @property
    def poster_url(self):
        if self.poster_path:
            return f"https://image.tmdb.org/t/p/w500{self.poster_path}"
        return None

    @property
    def backdrop_url(self):
        if self.backdrop_path:
            return f"https://image.tmdb.org/t/p/original{self.backdrop_path}"
        return None

    def __repr__(self):
        return f"<Movie {self.title} ({self.release_year})>"
