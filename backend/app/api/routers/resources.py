"""Resource management endpoints with file upload support."""

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db, require_roles
from app.core.response import success_response
from app.models.user import User
from app.schemas.resource import ResourceCreate, ResourceUpdate
from app.services.resource_service import ResourceService, _format_resource_item

router = APIRouter(prefix="/resources")


@router.get("")
async def list_resources(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    resource_type: str = Query(default=None),
    visibility: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List resources with pagination and filters.

    Resources are filtered by visibility (personal/school/region/system)
    and user's school context.
    """
    result = await ResourceService.list_resources(
        db=db,
        page=page,
        page_size=page_size,
        resource_type=resource_type,
        visibility=visibility,
        current_user=current_user,
    )
    return success_response(data=result)


@router.post("")
async def create_resource(
    data: ResourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Create a resource metadata record. Teacher only.

    To upload a file, use POST /resources/upload instead.
    """
    resource = await ResourceService.create_resource(db=db, data=data, user=current_user)
    return success_response(data=_format_resource_item(resource), message="资源创建成功")


@router.post("/upload")
async def upload_resource(
    title: str = Form(..., description="资源标题"),
    resource_type: str = Form(..., description="资源类型"),
    visibility: str = Form(default="school", description="可见范围"),
    file: UploadFile = File(..., description="上传的文件"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Upload a file and create a resource record. Teacher only.

    Files are saved to settings.UPLOAD_DIR with UUID filenames.
    Returns the created resource record with file info.
    """
    # Validate file size
    max_size = settings.MAX_UPLOAD_MB * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        from app.core.exceptions import AppException
        raise AppException(
            code=40000,
            message=f"文件大小超过限制 ({settings.MAX_UPLOAD_MB}MB)",
            status_code=413,
        )
    await file.seek(0)  # Reset so the service can read again

    resource = await ResourceService.upload_resource(
        db=db,
        title=title,
        resource_type=resource_type,
        file=file,
        visibility=visibility,
        user=current_user,
    )
    return success_response(data=_format_resource_item(resource), message="文件上传成功")


@router.get("/{resource_id}")
async def get_resource(
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get resource details by ID."""
    resource = await ResourceService.get_resource(db=db, resource_id=resource_id)
    return success_response(data=_format_resource_item(resource))


@router.patch("/{resource_id}")
async def update_resource(
    resource_id: str,
    data: ResourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Update a resource's metadata. Teacher only."""
    resource = await ResourceService.update_resource(
        db=db, resource_id=resource_id, data=data, user=current_user
    )
    return success_response(data=_format_resource_item(resource), message="资源更新成功")


@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Soft-delete a resource. Teacher only.

    The resource record is preserved but marked as deleted.
    """
    resource = await ResourceService.delete_resource(
        db=db, resource_id=resource_id, user=current_user
    )
    return success_response(data=_format_resource_item(resource), message="资源已删除")
