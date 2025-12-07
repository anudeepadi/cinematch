from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.movie import (
    MovieResponse,
    MovieListResponse,
    MovieListItem,
    MovieSearchQuery,
    GenreResponse
)
from app.services.movie_service import MovieService
from app.api.deps import OptionalUser
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("/", response_model=MovieListResponse)
async def get_movies(
    q: Optional[str] = Query(None, min_length=1, max_length=200),
    genres: Optional[List[int]] = Query(None),
    year_min: Optional[int] = Query(None, ge=1900, le=2030),
    year_max: Optional[int] = Query(None, ge=1900, le=2030),
    min_rating: Optional[float] = Query(None, ge=0, le=10),
    sort_by: str = Query("popularity"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: OptionalUser = None
):
    """Get paginated list of movies with optional filters"""
    query = MovieSearchQuery(
        q=q,
        genres=genres,
        year_min=year_min,
        year_max=year_max,
        min_rating=min_rating,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        per_page=per_page
    )

    service = MovieService(db)
    movies, total = await service.search_movies(query)

    return MovieListResponse(
        movies=[MovieListItem.model_validate(m) for m in movies],
        total=total,
        page=page,
        pages=(total + per_page - 1) // per_page,
        per_page=per_page
    )


@router.get("/trending", response_model=List[MovieListItem])
async def get_trending_movies(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get trending movies"""
    service = MovieService(db)
    movies = await service.get_trending_movies(limit)
    return [MovieListItem.model_validate(m) for m in movies]


@router.get("/top-rated", response_model=List[MovieListItem])
async def get_top_rated_movies(
    limit: int = Query(20, ge=1, le=100),
    min_votes: int = Query(100, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get top rated movies"""
    service = MovieService(db)
    movies = await service.get_top_rated_movies(limit, min_votes)
    return [MovieListItem.model_validate(m) for m in movies]


@router.get("/genres", response_model=List[GenreResponse])
async def get_genres(db: AsyncSession = Depends(get_db)):
    """Get all available genres"""
    service = MovieService(db)
    genres = await service.get_all_genres()
    return [GenreResponse.model_validate(g) for g in genres]


@router.get("/onboarding", response_model=List[MovieListItem])
async def get_onboarding_movies(
    count: int = Query(20, ge=5, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get diverse popular movies for onboarding quiz"""
    service = MovieService(db)
    movies = await service.get_movies_for_onboarding(count)
    return [MovieListItem.model_validate(m) for m in movies]


@router.get("/search", response_model=List[MovieListItem])
async def search_movies(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Quick search for movies by title"""
    service = MovieService(db)
    query = MovieSearchQuery(q=q, page=1, per_page=limit)
    movies, _ = await service.search_movies(query)
    return [MovieListItem.model_validate(m) for m in movies]


@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get movie details by ID"""
    service = MovieService(db)
    movie = await service.get_movie(movie_id)
    if not movie:
        raise NotFoundError("Movie")
    return MovieResponse.model_validate(movie)


@router.get("/{movie_id}/similar", response_model=List[MovieListItem])
async def get_similar_movies(
    movie_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get similar movies based on genres and keywords"""
    service = MovieService(db)
    movie = await service.get_movie(movie_id)
    if not movie:
        raise NotFoundError("Movie")

    similar = await service.get_similar_movies(movie_id, limit)
    return [MovieListItem.model_validate(m) for m in similar]


@router.get("/genre/{genre_id}", response_model=List[MovieListItem])
async def get_movies_by_genre(
    genre_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get movies by genre"""
    service = MovieService(db)
    movies = await service.get_movies_by_genre(genre_id, limit)
    return [MovieListItem.model_validate(m) for m in movies]
