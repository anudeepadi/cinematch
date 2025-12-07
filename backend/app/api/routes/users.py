from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    UserPreferencesUpdate,
    UserPreferencesResponse,
    OnboardingPreferences
)
from app.services.user_service import UserService
from app.api.deps import CurrentUser

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: CurrentUser):
    """Get current user profile"""
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    data: UserUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    service = UserService(db)
    user = await service.update_user(current_user, data)
    return UserResponse.model_validate(user)


@router.get("/me/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed user preferences"""
    service = UserService(db)
    prefs = await service.get_user_preferences(current_user.id)
    if not prefs:
        prefs = await service.create_user_preferences(current_user.id)
    return UserPreferencesResponse.model_validate(prefs)


@router.put("/me/preferences", response_model=UserResponse)
async def update_user_preferences(
    data: UserPreferencesUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Update user preferences"""
    service = UserService(db)
    user = await service.update_preferences(current_user, data)
    return UserResponse.model_validate(user)


@router.post("/me/onboarding", response_model=UserResponse)
async def complete_onboarding(
    data: OnboardingPreferences,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Complete onboarding and set initial preferences"""
    service = UserService(db)
    user = await service.process_onboarding(current_user, data)
    return UserResponse.model_validate(user)


@router.get("/me/stats")
async def get_user_stats(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Get user statistics"""
    from sqlalchemy import func, select
    from app.models.interaction import UserMovieInteraction, WatchHistory

    # Get interaction counts
    watch_result = await db.execute(
        select(func.count()).select_from(UserMovieInteraction).where(
            UserMovieInteraction.user_id == current_user.id,
            UserMovieInteraction.interaction_type == "watch"
        )
    )
    watchlist_count = watch_result.scalar() or 0

    pass_result = await db.execute(
        select(func.count()).select_from(UserMovieInteraction).where(
            UserMovieInteraction.user_id == current_user.id,
            UserMovieInteraction.interaction_type == "pass"
        )
    )
    passed_count = pass_result.scalar() or 0

    fav_result = await db.execute(
        select(func.count()).select_from(UserMovieInteraction).where(
            UserMovieInteraction.user_id == current_user.id,
            UserMovieInteraction.interaction_type == "favorite"
        )
    )
    favorites_count = fav_result.scalar() or 0

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

    return {
        "watchlist_count": watchlist_count,
        "passed_count": passed_count,
        "favorites_count": favorites_count,
        "watched_count": watched_count,
        "average_rating": round(avg_rating, 1) if avg_rating else None
    }
