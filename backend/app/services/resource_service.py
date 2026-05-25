"""Resource service: CRUD operations with file upload support."""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import ResourceNotFoundException, PermissionDeniedException
from app.models.resource import Resource
from app.models.user import User
from app.schemas.resource import ResourceCreate, ResourceUpdate


class ResourceService:
    """Service for resource management operations."""

    @staticmethod
    async def list_resources(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        resource_type: Optional[str] = None,
        visibility: Optional[str] = None,
        current_user: Optional[User] = None,
    ) -> dict:
        """List resources with pagination and optional filters.

        Users can see resources based on visibility:
        - personal: only the owner
        - school: same school
        - region: same region
        - system: everyone
        """
        query = select(Resource).options(selectinload(Resource.school))
        count_base = select(func.count()).select_from(Resource)

        if resource_type:
            query = query.where(Resource.resource_type == resource_type)
            count_base = count_base.where(Resource.resource_type == resource_type)
        if visibility:
            query = query.where(Resource.visibility == visibility)
            count_base = count_base.where(Resource.visibility == visibility)

        # RBAC filtering by visibility
        if current_user is not None and current_user.role != "system_admin":
            query = query.where(
                (Resource.visibility == "system")
                | ((Resource.visibility == "school") & (Resource.school_id == current_user.school_id))
                | ((Resource.visibility == "personal") & (Resource.school_id == current_user.school_id))
            )
            count_base = count_base.where(
                (Resource.visibility == "system")
                | ((Resource.visibility == "school") & (Resource.school_id == current_user.school_id))
                | ((Resource.visibility == "personal") & (Resource.school_id == current_user.school_id))
            )

        # Only return non-deleted
        query = query.where(Resource.deleted_at.is_(None))
        count_base = count_base.where(Resource.deleted_at.is_(None))

        total_result = await db.execute(count_base)
        total = total_result.scalar()

        offset = (page - 1) * page_size
        query = query.order_by(Resource.created_at.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        resources = result.unique().scalars().all()

        items = [_format_resource_item(r) for r in resources]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }

    @staticmethod
    async def create_resource(
        db: AsyncSession, data: ResourceCreate, user: User
    ) -> Resource:
        """Create a new resource metadata record."""
        metadata_val = data.metadata if data.metadata else {}

        resource = Resource(
            id=str(uuid.uuid4()),
            school_id=user.school_id,
            title=data.title,
            resource_type=data.resource_type,
            file_path=data.file_path,
            url=data.url,
            metadata_=metadata_val,
            visibility=data.visibility,
            status="active",
        )
        db.add(resource)
        await db.flush()
        await db.refresh(resource)
        return resource

    @staticmethod
    async def upload_resource(
        db: AsyncSession,
        title: str,
        resource_type: str,
        file,
        visibility: str,
        user: User,
    ) -> Resource:
        """Upload a file and create a resource record.

        Saves the file to settings.UPLOAD_DIR with a UUID filename.
        """
        # Ensure upload directory exists
        upload_dir = os.path.abspath(settings.UPLOAD_DIR)
        os.makedirs(upload_dir, exist_ok=True)

        # Generate unique filename
        ext = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_name = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(upload_dir, unique_name)

        # Read file content and save
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Build relative path for storage
        relative_path = unique_name

        resource = Resource(
            id=str(uuid.uuid4()),
            school_id=user.school_id,
            title=title,
            resource_type=resource_type,
            file_path=relative_path,
            url=None,
            metadata_={
                "original_filename": file.filename,
                "content_type": file.content_type,
                "size_bytes": len(content),
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            },
            visibility=visibility,
            status="active",
        )
        db.add(resource)
        await db.flush()
        await db.refresh(resource)
        return resource

    @staticmethod
    async def get_resource(db: AsyncSession, resource_id: str) -> Resource:
        """Get a resource by ID."""
        result = await db.execute(
            select(Resource)
            .options(selectinload(Resource.school))
            .where(Resource.id == resource_id, Resource.deleted_at.is_(None))
        )
        resource = result.unique().scalar_one_or_none()
        if resource is None:
            raise ResourceNotFoundException("资源不存在")
        return resource

    @staticmethod
    async def update_resource(
        db: AsyncSession, resource_id: str, data: ResourceUpdate, user: User
    ) -> Resource:
        """Update a resource's metadata."""
        resource = await ResourceService.get_resource(db, resource_id)

        update_data = data.model_dump(exclude_unset=True)
        # Map schema field 'metadata' to model column 'metadata_'
        if "metadata" in update_data and update_data["metadata"] is not None:
            setattr(resource, "metadata_", update_data.pop("metadata"))

        for key, value in update_data.items():
            if value is not None:
                setattr(resource, key, value)

        db.add(resource)
        await db.flush()
        await db.refresh(resource)
        return resource

    @staticmethod
    async def delete_resource(
        db: AsyncSession, resource_id: str, user: User
    ) -> Resource:
        """Soft-delete a resource."""
        resource = await ResourceService.get_resource(db, resource_id)

        # Only the resource owner or admin can delete
        if resource.school_id != user.school_id and user.role != "system_admin":
            raise PermissionDeniedException("只能删除自己学校的资源")

        resource.deleted_at = datetime.now(timezone.utc)
        resource.status = "deleted"
        db.add(resource)
        await db.flush()
        await db.refresh(resource)
        return resource


def _format_resource_item(resource: Resource) -> dict:
    """Format a resource model instance into a response dict."""
    return {
        "id": resource.id,
        "school_id": resource.school_id,
        "title": resource.title,
        "resource_type": resource.resource_type,
        "file_path": resource.file_path,
        "url": resource.url,
        "metadata": getattr(resource, "metadata_", None),
        "visibility": resource.visibility,
        "status": resource.status,
        "created_at": resource.created_at.isoformat() if resource.created_at else None,
        "updated_at": resource.updated_at.isoformat() if resource.updated_at else None,
    }
