"""Organization base-data services."""

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import PermissionDeniedException, ResourceNotFoundException
from app.models.class_ import Class
from app.models.region import Region
from app.models.school import School
from app.models.subject import Subject
from app.models.user import User
from app.schemas.org import (
    ClassCreate,
    ClassUpdate,
    RegionCreate,
    RegionUpdate,
    SchoolCreate,
    SchoolUpdate,
    SubjectCreate,
    SubjectUpdate,
)


class OrgService:
    """CRUD helpers for organization data."""

    @staticmethod
    async def list_regions(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
    ) -> dict:
        query = select(Region).where(Region.deleted_at.is_(None))
        count_query = select(func.count()).select_from(Region).where(Region.deleted_at.is_(None))
        if keyword:
            pattern = f"%{keyword}%"
            query = query.where(or_(Region.name.like(pattern), Region.code.like(pattern)))
            count_query = count_query.where(or_(Region.name.like(pattern), Region.code.like(pattern)))
        return await _paginate(db, query.order_by(Region.created_at.desc()), count_query, page, page_size, _region_to_dict)

    @staticmethod
    async def create_region(db: AsyncSession, data: RegionCreate) -> Region:
        region = Region(name=data.name, code=data.code)
        db.add(region)
        await db.flush()
        await db.refresh(region)
        return region

    @staticmethod
    async def update_region(db: AsyncSession, region_id: str, data: RegionUpdate) -> Region:
        region = await _get_active(db, Region, region_id, "Region not found")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(region, key, value)
        db.add(region)
        await db.flush()
        await db.refresh(region)
        return region

    @staticmethod
    async def delete_region(db: AsyncSession, region_id: str) -> Region:
        region = await _get_active(db, Region, region_id, "Region not found")
        region.deleted_at = datetime.now(timezone.utc)
        db.add(region)
        await db.flush()
        await db.refresh(region)
        return region

    @staticmethod
    async def list_schools(
        db: AsyncSession,
        user: User,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        region_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        query = select(School).options(selectinload(School.region)).where(School.deleted_at.is_(None))
        count_query = select(func.count()).select_from(School).where(School.deleted_at.is_(None))
        if user.role == "school_admin" and user.school_id:
            query = query.where(School.id == user.school_id)
            count_query = count_query.where(School.id == user.school_id)
        if keyword:
            pattern = f"%{keyword}%"
            query = query.where(or_(School.name.like(pattern), School.code.like(pattern)))
            count_query = count_query.where(or_(School.name.like(pattern), School.code.like(pattern)))
        if region_id:
            query = query.where(School.region_id == region_id)
            count_query = count_query.where(School.region_id == region_id)
        if status:
            query = query.where(School.status == status)
            count_query = count_query.where(School.status == status)
        return await _paginate(db, query.order_by(School.created_at.desc()), count_query, page, page_size, _school_to_dict)

    @staticmethod
    async def create_school(db: AsyncSession, data: SchoolCreate) -> School:
        await _get_active(db, Region, data.region_id, "Region not found")
        school = School(
            region_id=data.region_id,
            name=data.name,
            code=data.code,
            status=data.status,
        )
        db.add(school)
        await db.flush()
        await db.refresh(school)
        return school

    @staticmethod
    async def update_school(db: AsyncSession, school_id: str, data: SchoolUpdate) -> School:
        school = await _get_active(db, School, school_id, "School not found")
        update_data = data.model_dump(exclude_unset=True)
        if update_data.get("region_id"):
            await _get_active(db, Region, update_data["region_id"], "Region not found")
        for key, value in update_data.items():
            setattr(school, key, value)
        db.add(school)
        await db.flush()
        await db.refresh(school)
        return school

    @staticmethod
    async def delete_school(db: AsyncSession, school_id: str) -> School:
        school = await _get_active(db, School, school_id, "School not found")
        school.deleted_at = datetime.now(timezone.utc)
        school.status = "inactive"
        db.add(school)
        await db.flush()
        await db.refresh(school)
        return school

    @staticmethod
    async def list_classes(
        db: AsyncSession,
        user: User,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        school_id: Optional[str] = None,
        grade: Optional[str] = None,
    ) -> dict:
        query = select(Class).options(selectinload(Class.school)).where(Class.deleted_at.is_(None))
        count_query = select(func.count()).select_from(Class).where(Class.deleted_at.is_(None))
        scoped_school_id = user.school_id if user.role == "school_admin" else school_id
        if scoped_school_id:
            query = query.where(Class.school_id == scoped_school_id)
            count_query = count_query.where(Class.school_id == scoped_school_id)
        if keyword:
            pattern = f"%{keyword}%"
            query = query.where(or_(Class.name.like(pattern), Class.academic_year.like(pattern)))
            count_query = count_query.where(or_(Class.name.like(pattern), Class.academic_year.like(pattern)))
        if grade:
            query = query.where(Class.grade == grade)
            count_query = count_query.where(Class.grade == grade)
        return await _paginate(db, query.order_by(Class.created_at.desc()), count_query, page, page_size, _class_to_dict)

    @staticmethod
    async def create_class(db: AsyncSession, data: ClassCreate, user: User) -> Class:
        _ensure_school_scope(user, data.school_id)
        await _get_active(db, School, data.school_id, "School not found")
        class_item = Class(
            school_id=data.school_id,
            grade=data.grade,
            name=data.name,
            academic_year=data.academic_year,
        )
        db.add(class_item)
        await db.flush()
        await db.refresh(class_item)
        return class_item

    @staticmethod
    async def update_class(db: AsyncSession, class_id: str, data: ClassUpdate, user: User) -> Class:
        class_item = await _get_active(db, Class, class_id, "Class not found")
        _ensure_school_scope(user, class_item.school_id)
        update_data = data.model_dump(exclude_unset=True)
        if update_data.get("school_id"):
            _ensure_school_scope(user, update_data["school_id"])
            await _get_active(db, School, update_data["school_id"], "School not found")
        for key, value in update_data.items():
            setattr(class_item, key, value)
        db.add(class_item)
        await db.flush()
        await db.refresh(class_item)
        return class_item

    @staticmethod
    async def delete_class(db: AsyncSession, class_id: str, user: User) -> Class:
        class_item = await _get_active(db, Class, class_id, "Class not found")
        _ensure_school_scope(user, class_item.school_id)
        class_item.deleted_at = datetime.now(timezone.utc)
        db.add(class_item)
        await db.flush()
        await db.refresh(class_item)
        return class_item

    @staticmethod
    async def list_subjects(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> dict:
        query = select(Subject).where(Subject.deleted_at.is_(None))
        count_query = select(func.count()).select_from(Subject).where(Subject.deleted_at.is_(None))
        if keyword:
            pattern = f"%{keyword}%"
            query = query.where(Subject.name.like(pattern))
            count_query = count_query.where(Subject.name.like(pattern))
        if stage:
            query = query.where(Subject.stage == stage)
            count_query = count_query.where(Subject.stage == stage)
        return await _paginate(db, query.order_by(Subject.created_at.desc()), count_query, page, page_size, _subject_to_dict)

    @staticmethod
    async def create_subject(db: AsyncSession, data: SubjectCreate) -> Subject:
        subject = Subject(name=data.name, stage=data.stage)
        db.add(subject)
        await db.flush()
        await db.refresh(subject)
        return subject

    @staticmethod
    async def update_subject(db: AsyncSession, subject_id: str, data: SubjectUpdate) -> Subject:
        subject = await _get_active(db, Subject, subject_id, "Subject not found")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(subject, key, value)
        db.add(subject)
        await db.flush()
        await db.refresh(subject)
        return subject

    @staticmethod
    async def delete_subject(db: AsyncSession, subject_id: str) -> Subject:
        subject = await _get_active(db, Subject, subject_id, "Subject not found")
        subject.deleted_at = datetime.now(timezone.utc)
        db.add(subject)
        await db.flush()
        await db.refresh(subject)
        return subject


async def _get_active(db: AsyncSession, model: type[Any], item_id: str, message: str):
    result = await db.execute(
        select(model).where(model.id == item_id, model.deleted_at.is_(None))
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise ResourceNotFoundException(message)
    return item


async def _paginate(db: AsyncSession, query, count_query, page: int, page_size: int, formatter) -> dict:
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    items = result.unique().scalars().all()
    return {
        "items": [formatter(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
    }


def _ensure_school_scope(user: User, school_id: str) -> None:
    if user.role == "school_admin" and user.school_id and school_id != user.school_id:
        raise PermissionDeniedException("Cannot manage another school's classes")


def _region_to_dict(region: Region) -> dict:
    return {
        "id": region.id,
        "name": region.name,
        "code": region.code,
        "created_at": region.created_at.isoformat() if region.created_at else None,
        "updated_at": region.updated_at.isoformat() if region.updated_at else None,
    }


def _school_to_dict(school: School) -> dict:
    region = school.__dict__.get("region")
    return {
        "id": school.id,
        "region_id": school.region_id,
        "region_name": region.name if region else None,
        "name": school.name,
        "code": school.code,
        "status": school.status,
        "created_at": school.created_at.isoformat() if school.created_at else None,
        "updated_at": school.updated_at.isoformat() if school.updated_at else None,
    }


def _class_to_dict(class_item: Class) -> dict:
    school = class_item.__dict__.get("school")
    return {
        "id": class_item.id,
        "school_id": class_item.school_id,
        "school_name": school.name if school else None,
        "grade": class_item.grade,
        "name": class_item.name,
        "academic_year": class_item.academic_year,
        "created_at": class_item.created_at.isoformat() if class_item.created_at else None,
        "updated_at": class_item.updated_at.isoformat() if class_item.updated_at else None,
    }


def _subject_to_dict(subject: Subject) -> dict:
    return {
        "id": subject.id,
        "name": subject.name,
        "stage": subject.stage,
        "created_at": subject.created_at.isoformat() if subject.created_at else None,
        "updated_at": subject.updated_at.isoformat() if subject.updated_at else None,
    }
