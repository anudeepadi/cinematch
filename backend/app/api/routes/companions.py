from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.recommendation import CompanionLink
from app.schemas.companion import (
    CompanionLinkRequest,
    CompanionLinkResponse,
    CompanionResponse,
    CompanionPreferencesResponse,
    CompanionRequestResponse,
    CompanionRequestAction,
    CompanionListResponse
)
from app.api.deps import CurrentUser
from app.core.exceptions import NotFoundError, ConflictError, ValidationError

router = APIRouter()


@router.get("/", response_model=CompanionListResponse)
async def get_companions(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Get all linked companions and pending requests"""
    # Get accepted companions
    companions_result = await db.execute(
        select(CompanionLink, User).join(
            User, CompanionLink.companion_id == User.id
        ).where(
            CompanionLink.user_id == current_user.id,
            CompanionLink.status == "accepted"
        )
    )
    companions = [
        CompanionResponse(
            id=link.id,
            user_id=link.user_id,
            companion_id=link.companion_id,
            nickname=link.nickname,
            status=link.status,
            companion_username=user.username,
            companion_avatar=user.avatar_url,
            created_at=link.created_at
        )
        for link, user in companions_result.all()
    ]

    # Get pending requests received
    pending_result = await db.execute(
        select(CompanionLink, User).join(
            User, CompanionLink.user_id == User.id
        ).where(
            CompanionLink.companion_id == current_user.id,
            CompanionLink.status == "pending"
        )
    )
    pending_requests = [
        CompanionRequestResponse(
            id=link.id,
            from_user_id=link.user_id,
            from_username=user.username,
            from_avatar=user.avatar_url,
            nickname=link.nickname,
            created_at=link.created_at
        )
        for link, user in pending_result.all()
    ]

    # Get sent requests
    sent_result = await db.execute(
        select(CompanionLink, User).join(
            User, CompanionLink.companion_id == User.id
        ).where(
            CompanionLink.user_id == current_user.id,
            CompanionLink.status == "pending"
        )
    )
    sent_requests = [
        CompanionLinkResponse(
            id=link.id,
            status=link.status,
            companion_email=user.email,
            nickname=link.nickname,
            created_at=link.created_at
        )
        for link, user in sent_result.all()
    ]

    return CompanionListResponse(
        companions=companions,
        pending_requests=pending_requests,
        sent_requests=sent_requests
    )


@router.post("/link", response_model=CompanionLinkResponse)
async def send_companion_link_request(
    request: CompanionLinkRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Send a companion link request to another user"""
    # Find target user
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    companion = result.scalar_one_or_none()

    if not companion:
        raise NotFoundError("User with this email not found")

    if companion.id == current_user.id:
        raise ValidationError("Cannot link with yourself")

    # Check if link already exists
    existing = await db.execute(
        select(CompanionLink).where(
            or_(
                (CompanionLink.user_id == current_user.id) & (CompanionLink.companion_id == companion.id),
                (CompanionLink.user_id == companion.id) & (CompanionLink.companion_id == current_user.id)
            )
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError("Companion link already exists or pending")

    # Create link request
    link = CompanionLink(
        user_id=current_user.id,
        companion_id=companion.id,
        nickname=request.nickname,
        status="pending"
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)

    return CompanionLinkResponse(
        id=link.id,
        status=link.status,
        companion_email=companion.email,
        nickname=link.nickname,
        created_at=link.created_at
    )


@router.post("/requests/{request_id}/respond")
async def respond_to_companion_request(
    request_id: int,
    action: CompanionRequestAction,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Accept or reject a companion link request"""
    result = await db.execute(
        select(CompanionLink).where(
            CompanionLink.id == request_id,
            CompanionLink.companion_id == current_user.id,
            CompanionLink.status == "pending"
        )
    )
    link = result.scalar_one_or_none()

    if not link:
        raise NotFoundError("Companion request")

    if action.action == "accept":
        link.status = "accepted"
        link.accepted_at = datetime.utcnow()

        # Create reverse link
        reverse_link = CompanionLink(
            user_id=current_user.id,
            companion_id=link.user_id,
            status="accepted",
            accepted_at=datetime.utcnow()
        )
        db.add(reverse_link)
    else:
        link.status = "rejected"

    link.updated_at = datetime.utcnow()
    await db.commit()

    return {"status": link.status, "message": f"Request {action.action}ed"}


@router.delete("/{companion_id}")
async def remove_companion(
    companion_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Remove a companion link"""
    # Find and delete both directions of the link
    result = await db.execute(
        select(CompanionLink).where(
            or_(
                (CompanionLink.user_id == current_user.id) & (CompanionLink.companion_id == companion_id),
                (CompanionLink.user_id == companion_id) & (CompanionLink.companion_id == current_user.id)
            )
        )
    )
    links = result.scalars().all()

    if not links:
        raise NotFoundError("Companion link")

    for link in links:
        await db.delete(link)

    await db.commit()
    return {"message": "Companion removed"}


@router.get("/{companion_id}/preferences", response_model=CompanionPreferencesResponse)
async def get_companion_preferences(
    companion_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Get companion's preferences for joint recommendations"""
    # Verify companion link exists
    result = await db.execute(
        select(CompanionLink).where(
            CompanionLink.user_id == current_user.id,
            CompanionLink.companion_id == companion_id,
            CompanionLink.status == "accepted"
        )
    )
    if not result.scalar_one_or_none():
        raise NotFoundError("Companion link")

    # Get companion's preferences
    companion_result = await db.execute(
        select(User).where(User.id == companion_id)
    )
    companion = companion_result.scalar_one_or_none()

    if not companion:
        raise NotFoundError("Companion")

    return CompanionPreferencesResponse(
        companion_id=companion.id,
        username=companion.username,
        preferred_genres=companion.preferred_genres or [],
        year_range_min=companion.year_range_min,
        year_range_max=companion.year_range_max,
        mood_action=companion.mood_action,
        mood_comedy=companion.mood_comedy,
        mood_drama=companion.mood_drama,
        mood_horror=companion.mood_horror,
        mood_romance=companion.mood_romance,
        mood_scifi=companion.mood_scifi,
        mood_thriller=companion.mood_thriller,
        mood_documentary=companion.mood_documentary
    )
