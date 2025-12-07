from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class GenreResponse(BaseModel):
    """Schema for genre response"""
    id: int
    tmdb_id: int
    name: str

    class Config:
        from_attributes = True


class CastMember(BaseModel):
    """Schema for cast member"""
    id: int
    name: str
    character: Optional[str] = None
    profile_path: Optional[str] = None


class Director(BaseModel):
    """Schema for director"""
    id: int
    name: str


class MovieResponse(BaseModel):
    """Full movie response schema"""
    id: int
    tmdb_id: int
    imdb_id: Optional[str] = None
    title: str
    original_title: Optional[str] = None
    tagline: Optional[str] = None
    overview: Optional[str] = None
    release_date: Optional[datetime] = None
    release_year: Optional[int] = None
    runtime: Optional[int] = None
    vote_average: float = 0.0
    vote_count: int = 0
    popularity: float = 0.0
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    original_language: str = "en"
    spoken_languages: List[str] = []
    production_countries: List[str] = []
    genres: List[GenreResponse] = []
    cast: List[CastMember] = []
    directors: List[Director] = []
    keywords: List[str] = []
    mood_scores: Dict[str, float] = {}
    is_adult: bool = False
    status: str = "Released"

    class Config:
        from_attributes = True


class MovieListItem(BaseModel):
    """Simplified movie for list views"""
    id: int
    tmdb_id: int
    title: str
    overview: Optional[str] = None
    release_year: Optional[int] = None
    vote_average: float = 0.0
    poster_path: Optional[str] = None
    poster_url: Optional[str] = None
    backdrop_path: Optional[str] = None
    backdrop_url: Optional[str] = None
    genres: List[GenreResponse] = []

    class Config:
        from_attributes = True


class MovieListResponse(BaseModel):
    """Paginated movie list response"""
    movies: List[MovieListItem]
    total: int
    page: int
    pages: int
    per_page: int


class MovieSearchQuery(BaseModel):
    """Query parameters for movie search"""
    q: Optional[str] = Field(None, min_length=1, max_length=200)
    genres: Optional[List[int]] = None
    year_min: Optional[int] = Field(None, ge=1900, le=2030)
    year_max: Optional[int] = Field(None, ge=1900, le=2030)
    min_rating: Optional[float] = Field(None, ge=0, le=10)
    sort_by: Optional[str] = Field("popularity", pattern=r"^(popularity|vote_average|release_date|title)$")
    sort_order: Optional[str] = Field("desc", pattern=r"^(asc|desc)$")
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class MovieCreate(BaseModel):
    """Schema for creating/updating a movie from TMDB data"""
    tmdb_id: int
    imdb_id: Optional[str] = None
    title: str
    original_title: Optional[str] = None
    tagline: Optional[str] = None
    overview: Optional[str] = None
    release_date: Optional[datetime] = None
    release_year: Optional[int] = None
    runtime: Optional[int] = None
    vote_average: float = 0.0
    vote_count: int = 0
    popularity: float = 0.0
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    original_language: str = "en"
    spoken_languages: List[str] = []
    production_countries: List[str] = []
    genre_ids: List[int] = []
    cast: List[Dict] = []
    directors: List[Dict] = []
    keywords: List[str] = []
    mood_scores: Dict[str, float] = {}
    is_adult: bool = False
    status: str = "Released"
