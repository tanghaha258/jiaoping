"""Organization base-data endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_roles
from app.core.response import success_response
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
from app.services.org_service import (
    OrgService,
    _class_to_dict,
    _region_to_dict,
    _school_to_dict,
    _subject_to_dict,
)

router = APIRouter(prefix="/org")


@router.get("/regions")
async def list_regions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "region_admin", "school_admin")),
):
    result = await OrgService.list_regions(db, page=page, page_size=page_size, keyword=keyword)
    return success_response(result)


@router.post("/regions")
async def create_region(
    data: RegionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "region_admin")),
):
    region = await OrgService.create_region(db, data)
    return success_response(_region_to_dict(region), message="Region created")


@router.patch("/regions/{region_id}")
async def update_region(
    region_id: str,
    data: RegionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "region_admin")),
):
    region = await OrgService.update_region(db, region_id, data)
    return success_response(_region_to_dict(region), message="Region updated")


@router.delete("/regions/{region_id}")
async def delete_region(
    region_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "region_admin")),
):
    region = await OrgService.delete_region(db, region_id)
    return success_response(_region_to_dict(region), message="Region deleted")


@router.get("/schools")
async def list_schools(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: Optional[str] = Query(default=None),
    region_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "region_admin", "school_admin")),
):
    result = await OrgService.list_schools(
        db,
        current_user,
        page=page,
        page_size=page_size,
        keyword=keyword,
        region_id=region_id,
        status=status,
    )
    return success_response(result)


@router.post("/schools")
async def create_school(
    data: SchoolCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "region_admin")),
):
    school = await OrgService.create_school(db, data)
    return success_response(_school_to_dict(school), message="School created")


@router.patch("/schools/{school_id}")
async def update_school(
    school_id: str,
    data: SchoolUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "region_admin")),
):
    school = await OrgService.update_school(db, school_id, data)
    return success_response(_school_to_dict(school), message="School updated")


@router.delete("/schools/{school_id}")
async def delete_school(
    school_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "region_admin")),
):
    school = await OrgService.delete_school(db, school_id)
    return success_response(_school_to_dict(school), message="School deleted")


@router.get("/classes")
async def list_classes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: Optional[str] = Query(default=None),
    school_id: Optional[str] = Query(default=None),
    grade: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "school_admin", "teacher")),
):
    result = await OrgService.list_classes(
        db,
        current_user,
        page=page,
        page_size=page_size,
        keyword=keyword,
        school_id=school_id,
        grade=grade,
    )
    return success_response(result)


@router.post("/classes")
async def create_class(
    data: ClassCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "school_admin")),
):
    class_item = await OrgService.create_class(db, data, current_user)
    return success_response(_class_to_dict(class_item), message="Class created")


@router.patch("/classes/{class_id}")
async def update_class(
    class_id: str,
    data: ClassUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "school_admin")),
):
    class_item = await OrgService.update_class(db, class_id, data, current_user)
    return success_response(_class_to_dict(class_item), message="Class updated")


@router.delete("/classes/{class_id}")
async def delete_class(
    class_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "school_admin")),
):
    class_item = await OrgService.delete_class(db, class_id, current_user)
    return success_response(_class_to_dict(class_item), message="Class deleted")


@router.get("/subjects")
async def list_subjects(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: Optional[str] = Query(default=None),
    stage: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "school_admin", "teacher")),
):
    result = await OrgService.list_subjects(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        stage=stage,
    )
    return success_response(result)


@router.post("/subjects")
async def create_subject(
    data: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin")),
):
    subject = await OrgService.create_subject(db, data)
    return success_response(_subject_to_dict(subject), message="Subject created")


@router.patch("/subjects/{subject_id}")
async def update_subject(
    subject_id: str,
    data: SubjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin")),
):
    subject = await OrgService.update_subject(db, subject_id, data)
    return success_response(_subject_to_dict(subject), message="Subject updated")


@router.delete("/subjects/{subject_id}")
async def delete_subject(
    subject_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin")),
):
    subject = await OrgService.delete_subject(db, subject_id)
    return success_response(_subject_to_dict(subject), message="Subject deleted")
