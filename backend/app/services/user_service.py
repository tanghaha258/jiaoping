"""User service: CRUD operations for users."""

from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.exceptions import ResourceNotFoundException
from app.core.security import hash_password
from app.models.class_ import Class
from app.models.school import School
from app.models.user import User
from app.schemas.user import UserCreate, UserDataImportRequest, UserPackageItem, UserUpdate


class UserService:
    """Service for user management operations."""

    @staticmethod
    async def list_users(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        """List users with pagination and optional filters."""
        query = select(User).options(joinedload(User.school))

        if keyword:
            pattern = f"%{keyword}%"
            query = query.where(or_(User.username.like(pattern), User.name.like(pattern)))
        if role:
            query = query.where(User.role == role)
        if status:
            query = query.where(User.status == status)

        # Count total
        count_query = select(func.count()).select_from(User)
        if keyword:
            pattern = f"%{keyword}%"
            count_query = count_query.where(or_(User.username.like(pattern), User.name.like(pattern)))
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

    @staticmethod
    async def reset_password(db: AsyncSession, user_id: str, new_password: str) -> User:
        """Reset a user's password as an administrator."""
        user = await UserService.get_user(db, user_id)
        user.password_hash = hash_password(new_password)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    def template_data_package() -> dict:
        """Return a portable account import template."""
        return {
            "users": [
                {
                    "username": "qz-teacher-001",
                    "name": "Sample Teacher",
                    "role": "teacher",
                    "school_code": "qz01",
                    "class": None,
                    "initial_password": "password",
                },
                {
                    "username": "qz-student-001",
                    "name": "Sample Student",
                    "role": "student",
                    "school_code": "qz01",
                    "class": {
                        "grade": "grade_7",
                        "name": "Class 1",
                        "academic_year": "2025-2026",
                    },
                    "initial_password": "password",
                },
            ]
        }

    @staticmethod
    async def export_data_package(db: AsyncSession) -> dict:
        """Export user accounts without password material."""
        result = await db.execute(
            select(User)
            .options(joinedload(User.school), joinedload(User.student_class))
            .where(User.deleted_at.is_(None))
            .order_by(User.username.asc())
        )
        users = result.unique().scalars().all()
        return {"users": [_user_to_package_item(user) for user in users]}

    @staticmethod
    async def import_data_package(db: AsyncSession, request: UserDataImportRequest) -> dict:
        """Validate or import a portable user account package."""
        summary = _empty_user_import_summary(request.dry_run)
        seen_usernames: set[str] = set()
        schools_by_code = await _active_schools_by_code(db)
        existing_users = await _active_users_by_username(db)
        allowed_roles = {"school_admin", "researcher", "teacher", "student"}

        for index, item in enumerate(request.package.users, start=1):
            row_label = f"Row {index} ({item.username})"
            if item.username in seen_usernames:
                summary["errors"].append(f"{row_label}: duplicate username in package")
                continue
            seen_usernames.add(item.username)

            if item.username in existing_users:
                summary["skipped"]["users"] += 1
                continue

            if item.role not in allowed_roles:
                summary["errors"].append(f"{row_label}: unsupported role {item.role}")
                continue

            if not item.initial_password:
                summary["errors"].append(f"{row_label}: initial_password is required")
                continue

            school = schools_by_code.get(item.school_code)
            if school is None:
                summary["errors"].append(f"{row_label}: missing school {item.school_code}")
                continue

            class_id = None
            if item.role == "student":
                if item.class_ref is None:
                    summary["errors"].append(f"{row_label}: student class is required")
                    continue
                class_item = await _find_class(db, school.id, item)
                if class_item is None:
                    summary["errors"].append(
                        f"{row_label}: missing class {item.class_ref.grade} {item.class_ref.name} "
                        f"{item.class_ref.academic_year}"
                    )
                    continue
                class_id = class_item.id

            summary["created"]["users"] += 1
            if not request.dry_run:
                user = User(
                    username=item.username,
                    password_hash=hash_password(item.initial_password),
                    name=item.name,
                    role=item.role,
                    school_id=school.id,
                    class_id=class_id,
                    status="active",
                )
                db.add(user)
                await db.flush()
                existing_users[item.username] = user
                summary["initial_passwords"].append(
                    {
                        "username": item.username,
                        "name": item.name,
                        "role": item.role,
                        "initial_password": item.initial_password,
                    }
                )

        if not request.dry_run:
            await db.flush()

        return summary


def _user_to_package_item(user: User) -> dict:
    school = user.__dict__.get("school")
    class_item = user.__dict__.get("student_class")
    class_ref = None
    if class_item:
        class_ref = {
            "grade": class_item.grade,
            "name": class_item.name,
            "academic_year": class_item.academic_year,
        }
    return {
        "username": user.username,
        "name": user.name,
        "role": user.role,
        "school_code": school.code if school else "",
        "class": class_ref,
        "status": user.status,
    }


def _empty_user_import_summary(dry_run: bool) -> dict:
    return {
        "dry_run": dry_run,
        "created": {"users": 0},
        "skipped": {"users": 0},
        "errors": [],
        "initial_passwords": [],
    }


async def _active_schools_by_code(db: AsyncSession) -> dict[str, School]:
    result = await db.execute(
        select(School).where(School.deleted_at.is_(None), School.status == "active")
    )
    return {item.code: item for item in result.scalars().all()}


async def _active_users_by_username(db: AsyncSession) -> dict[str, User]:
    result = await db.execute(select(User).where(User.deleted_at.is_(None)))
    return {item.username: item for item in result.scalars().all()}


async def _find_class(db: AsyncSession, school_id: str, item: UserPackageItem) -> Class | None:
    if item.class_ref is None:
        return None
    result = await db.execute(
        select(Class).where(
            Class.deleted_at.is_(None),
            Class.school_id == school_id,
            Class.grade == item.class_ref.grade,
            Class.name == item.class_ref.name,
            Class.academic_year == item.class_ref.academic_year,
        )
    )
    return result.scalar_one_or_none()
