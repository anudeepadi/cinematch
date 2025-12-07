from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.interaction import (
    InteractionCreate,
    InteractionResponse,
    InteractionWithMovie,
    WatchHistoryCreate,
    WatchHistoryResponse,
    WatchlistResponse,
    InteractionHistoryResponse,
    InteractionStats
)
from app.schemas.movie import MovieListItem
from app.services.interaction_service import InteractionService
from app.api.deps import CurrentUser

router = APIRouter()


@router.post("/", response_model=InteractionResponse)
async def create_interaction(
    data: InteractionCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Record a user interaction with a movie (watch/pass/favorite)"""
    service = InteractionService(db)
    interaction = await service.create_interaction(current_user.id, data)
    return InteractionResponse.model_validate(interaction)


@router.post("/watched", response_model=WatchHistoryResponse)
async def add_watched_movie(
    data: WatchHistoryCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Add a movie to watch history with rating and feedback"""
    service = InteractionService(db)
    history = await service.add_to_watch_history(current_user.id, data)
    return WatchHistoryResponse.model_validate(history)


@router.get("/history", response_model=InteractionHistoryResponse)
async def get_interaction_history(
    interaction_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db)
):
    """Get user's interaction history"""
    service = InteractionService(db)
    offset = (page - 1) * per_page
    interactions, total = await service.get_user_interactions(
        current_user.id,
        interaction_type=interaction_type,
        limit=per_page,
        offset=offset
    )

    return InteractionHistoryResponse(
        interactions=[
            InteractionWithMovie(
                id=i.id,
                interaction_type=i.interaction_type,
                rating=i.rating,
                mood_at_interaction=i.mood_at_interaction,
                watching_with=i.watching_with,
                created_at=i.created_at,
                movie=MovieListItem.model_validate(i.movie)
            )
            for i in interactions
        ],
        total=total,
        page=page,
        pages=(total + per_page - 1) // per_page
    )


@router.get("/watchlist", response_model=WatchlistResponse)
async def get_watchlist(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Get user's watchlist (movies marked to watch)"""
    service = InteractionService(db)
    movies = await service.get_watchlist(current_user.id)
    return WatchlistResponse(
        movies=[MovieListItem.model_validate(m) for m in movies],
        total=len(movies)
    )


@router.get("/watched", response_model=WatchlistResponse)
async def get_watched(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Get user's watched movies"""
    service = InteractionService(db)
    movies = await service.get_watched(current_user.id)
    return WatchlistResponse(
        movies=[MovieListItem.model_validate(m) for m in movies],
        total=len(movies)
    )


@router.get("/favorites", response_model=WatchlistResponse)
async def get_favorites(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Get user's favorite movies"""
    service = InteractionService(db)
    movies = await service.get_favorites(current_user.id)
    return WatchlistResponse(
        movies=[MovieListItem.model_validate(m) for m in movies],
        total=len(movies)
    )


@router.delete("/watchlist/{movie_id}")
async def remove_from_watchlist(
    movie_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Remove a movie from watchlist"""
    service = InteractionService(db)
    removed = await service.remove_from_watchlist(current_user.id, movie_id)
    return {"removed": removed}


@router.get("/stats", response_model=InteractionStats)
async def get_interaction_stats(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Get user's interaction statistics"""
    from sqlalchemy import func, select
    from app.models.interaction import UserMovieInteraction, WatchHistory

    # Get counts
    watchlist_result = await db.execute(
        select(func.count()).select_from(UserMovieInteraction).where(
            UserMovieInteraction.user_id == current_user.id,
            UserMovieInteraction.interaction_type == "watch"
        )
    )
    watchlist_count = watchlist_result.scalar() or 0

    passed_result = await db.execute(
        select(func.count()).select_from(UserMovieInteraction).where(
            UserMovieInteraction.user_id == current_user.id,
            UserMovieInteraction.interaction_type == "pass"
        )
    )
    passed_count = passed_result.scalar() or 0

    favorites_result = await db.execute(
        select(func.count()).select_from(UserMovieInteraction).where(
            UserMovieInteraction.user_id == current_user.id,
            UserMovieInteraction.interaction_type == "favorite"
        )
    )
    favorites_count = favorites_result.scalar() or 0

    watched_result = await db.execute(
        select(func.count()).select_from(WatchHistory).where(
            WatchHistory.user_id == current_user.id
        )
    )
    watched_count = watched_result.scalar() or 0

    avg_rating_result = await db.execute(
        select(func.avg(WatchHistory.rating)).where(
            WatchHistory.user_id == current_user.id,
            WatchHistory.rating.isnot(None)
        )
    )
    avg_rating = avg_rating_result.scalar()

    return InteractionStats(
        total_watched=watched_count,
        total_watchlist=watchlist_count,
        total_passed=passed_count,
        total_favorites=favorites_count,
        average_rating=round(avg_rating, 1) if avg_rating else None
    )
