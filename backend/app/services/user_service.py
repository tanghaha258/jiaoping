"""User service: CRUD operations for users."""

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.exceptions import ResourceNotFoundException
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service for user management operations."""

    @staticmethod
    async def list_users(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        """List users with pagination and optional filters."""
        query = select(User).options(joinedload(User.school))

        if role:
            query = query.where(User.role == role)
        if status:
            query = query.where(User.status == status)

        # Count total
        count_query = select(func.count()).select_from(User)
        if role:
            count_query = count_query.where(User.role == role)
        if status:
            count_query = count_query.where(User.status == status)
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Fetch page
        offset = (page - 1) * page_size
        query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        users = result.unique().scalars().all()

        items = []
        for user in users:
            items.append({
                "id": user.id,
                "username": user.username,
                "name": user.name,
                "role": user.role,
                "school_id": user.school_id,
                "school_name": user.school.name if user.school else None,
                "class_id": user.class_id,
                "status": user.status,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }

    @staticmethod
    async def create_user(db: AsyncSession, data: UserCreate) -> User:
        """Create a new user."""
        # Check if username already exists
        result = await db.execute(
            select(User).where(User.username == data.username)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ResourceNotFoundException(f"用户名 '{data.username}' 已存在")

        user = User(
            username=data.username,
            password_hash=hash_password(data.password),
            name=data.name,
            role=data.role,
            school_id=data.school_id,
            class_id=data.class_id,
            status="active",
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_user(db: AsyncSession, user_id: str) -> User:
        """Get a user by ID."""
        result = await db.execute(
            select(User).options(joinedload(User.school)).where(User.id == user_id)
        )
        user = result.unique().scalar_one_or_none()
        if user is None:
            raise ResourceNotFoundException("用户不存在")
        return user

    @staticmethod
    async def update_user(db: AsyncSession, user_id: str, data: UserUpdate) -> User:
        """Update user fields."""
        user = await UserService.get_user(db, user_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)

        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def change_user_status(db: AsyncSession, user_id: str, status: str) -> User:
        """Change a user's account status."""
        user = await UserService.get_user(db, user_id)
        user.status = status
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
