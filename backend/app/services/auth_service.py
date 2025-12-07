from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.interaction import UserPreference
from app.schemas.auth import UserCreate
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import ConflictError, AuthenticationError


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, user_data: UserCreate) -> tuple[User, str]:
        """Register a new user and return the user with access token"""
        # Check if email exists
        existing = await self.db.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing.scalar_one_or_none():
            raise ConflictError("Email already registered")

        # Check if username exists
        existing = await self.db.execute(
            select(User).where(User.username == user_data.username)
        )
        if existing.scalar_one_or_none():
            raise ConflictError("Username already taken")

        # Create user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # Create initial preferences
        preferences = UserPreference(user_id=user.id)
        self.db.add(preferences)
        await self.db.commit()

        # Generate token
        access_token = create_access_token(subject=user.id)

        return user, access_token

    async def authenticate_user(self, email: str, password: str) -> tuple[User, str]:
        """Authenticate user and return user with access token"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        # Update last login
        user.last_login = datetime.utcnow()
        await self.db.commit()

        # Generate token
        access_token = create_access_token(subject=user.id)

        return user, access_token

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
