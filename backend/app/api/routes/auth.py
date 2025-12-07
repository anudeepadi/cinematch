from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import UserCreate, UserLogin, Token, AuthResponse, UserBasicResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.api.deps import CurrentUser

router = APIRouter()


@router.post("/register", response_model=AuthResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    auth_service = AuthService(db)
    user, access_token = await auth_service.register_user(user_data)

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserBasicResponse.model_validate(user)
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login and get access token"""
    auth_service = AuthService(db)
    user, access_token = await auth_service.authenticate_user(
        credentials.email,
        credentials.password
    )

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserBasicResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser
):
    """Get current authenticated user info"""
    return UserResponse.model_validate(current_user)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: CurrentUser
):
    """Refresh access token"""
    from app.core.security import create_access_token
    access_token = create_access_token(subject=current_user.id)
    return Token(access_token=access_token)


@router.post("/logout")
async def logout():
    """Logout (client should discard token)"""
    return {"message": "Successfully logged out"}
