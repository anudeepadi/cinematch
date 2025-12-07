from typing import Annotated, Optional
from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.core.security import verify_token
from app.core.exceptions import AuthenticationError, NotFoundError

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """Get the current authenticated user from JWT token"""
    if not credentials:
        raise AuthenticationError("Missing authentication token")

    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise AuthenticationError("Invalid or expired token")

    user_id = payload.get("sub")
    if user_id is None:
        raise AuthenticationError("Invalid token payload")

    try:
        user_id = int(user_id)
    except ValueError:
        raise AuthenticationError("Invalid user ID in token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundError("User")

    if not user.is_active:
        raise AuthenticationError("User account is deactivated")

    return user


async def get_current_user_optional(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Optional[User]:
    """Get the current user if authenticated, otherwise return None"""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except AuthenticationError:
        return None


# Type aliases for cleaner dependency injection
DBSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[Optional[User], Depends(get_current_user_optional)]
