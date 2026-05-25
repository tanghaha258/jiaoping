"""Project service: CRUD operations, state transitions, and relationship management."""

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    InvalidStateTransitionException,
    PermissionDeniedException,
    ResourceNotFoundException,
)
from app.models.project import Project
from app.models.project_subject import ProjectSubject
from app.models.project_class import ProjectClass
from app.models.subject import Subject
from app.models.user import User
from app.models.class_ import Class
from app.schemas.project import ProjectCreate, ProjectUpdate


# Valid state transitions
PROJECT_TRANSITIONS = {
    "draft": "active",
    "active": "completed",
    "completed": "archived",
}


class ProjectService:
    """Service for project management operations."""

    @staticmethod
    async def list_projects(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        grade: Optional[str] = None,
        current_user: Optional[User] = None,
    ) -> dict:
        """List projects with pagination and optional filters.

        Teachers see their own projects plus those authorized to their school.
        Admins see all projects in their school.
        """
        query = (
            select(Project)
            .options(
                selectinload(Project.subjects).selectinload(ProjectSubject.subject),
                selectinload(Project.classes).selectinload(ProjectClass.target_class),
                selectinload(Project.owner),
            )
        )
        count_base = select(func.count()).select_from(Project)

        # Apply filters
        if status:
            query = query.where(Project.status == status)
            count_base = count_base.where(Project.status == status)
        if grade:
            query = query.where(Project.grade == grade)
            count_base = count_base.where(Project.grade == grade)

        # RBAC filtering
        if current_user is not None:
            if current_user.role == "teacher":
                # Teacher sees own projects + same-school projects
                query = query.where(
                    (Project.owner_id == current_user.id)
                    | (
                        (Project.school_id == current_user.school_id)
                        & (Project.status != "draft")
                    )
                )
                count_base = count_base.where(
                    (Project.owner_id == current_user.id)
                    | (
                        (Project.school_id == current_user.school_id)
                        & (Project.status != "draft")
                    )
                )
            elif current_user.role == "student":
                # Student sees active/completed projects in their class
                query = query.where(
                    (Project.school_id == current_user.school_id)
                    & (Project.status.in_(["active", "completed"]))
                )
                count_base = count_base.where(
                    (Project.school_id == current_user.school_id)
                    & (Project.status.in_(["active", "completed"]))
                )
            elif current_user.role == "system_admin":
                # Admin sees all - no additional filter
                pass
        # else: no user context, show all (shouldn't happen for this endpoint)

        # Get total count
        total_result = await db.execute(count_base)
        total = total_result.scalar()

        # Fetch page
        offset = (page - 1) * page_size
        query = query.order_by(Project.created_at.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        projects = result.unique().scalars().all()

        items = []
        for project in projects:
            items.append(_format_project_item(project))

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }

    @staticmethod
    async def create_project(
        db: AsyncSession, data: ProjectCreate, user: User
    ) -> Project:
        """Create a new project with its subject and class associations."""
        project = Project(
            id=str(uuid.uuid4()),
            school_id=user.school_id,
            name=data.name,
            grade=data.grade,
            driving_question=data.driving_question,
            objectives=data.objectives,
            lesson_count=data.lesson_count,
            status="draft",
            owner_id=user.id,
        )
        db.add(project)

        # Create project-subject associations
        for subject_id in data.subject_ids:
            # Verify subject exists
            subj_result = await db.execute(
                select(Subject).where(Subject.id == subject_id)
            )
            if subj_result.scalar_one_or_none() is None:
                raise ResourceNotFoundException(f"学科 {subject_id} 不存在")
            ps = ProjectSubject(project_id=project.id, subject_id=subject_id)
            db.add(ps)

        # Create project-class associations
        for class_id in data.class_ids:
            cls_result = await db.execute(
                select(Class).where(Class.id == class_id)
            )
            if cls_result.scalar_one_or_none() is None:
                raise ResourceNotFoundException(f"班级 {class_id} 不存在")
            pc = ProjectClass(project_id=project.id, class_id=class_id)
            db.add(pc)

        await db.flush()
        await db.refresh(project)
        return project

    @staticmethod
    async def get_project(db: AsyncSession, project_id: str) -> Project:
        """Get a project by ID with all relationships eager-loaded."""
        result = await db.execute(
            select(Project)
            .options(
                selectinload(Project.subjects).selectinload(ProjectSubject.subject),
                selectinload(Project.classes).selectinload(ProjectClass.target_class),
                selectinload(Project.owner),
                selectinload(Project.tasks),
            )
            .where(Project.id == project_id)
        )
        project = result.unique().scalar_one_or_none()
        if project is None:
            raise ResourceNotFoundException("项目不存在")
        return project

    @staticmethod
    async def update_project(
        db: AsyncSession, project_id: str, data: ProjectUpdate
    ) -> Project:
        """Update project fields and optionally its subject/class associations."""
        project = await ProjectService.get_project(db, project_id)

        update_data = data.model_dump(exclude_unset=True)
        subject_ids = update_data.pop("subject_ids", None)
        class_ids = update_data.pop("class_ids", None)

        for key, value in update_data.items():
            if value is not None:
                setattr(project, key, value)

        # Update subjects if provided
        if subject_ids is not None:
            # Remove existing associations
            existing_subs = (
                await db.execute(
                    select(ProjectSubject).where(
                        ProjectSubject.project_id == project_id
                    )
                )
            ).scalars().all()
            for ps in existing_subs:
                await db.delete(ps)

            # Add new ones
            for subject_id in subject_ids:
                ps = ProjectSubject(project_id=project_id, subject_id=subject_id)
                db.add(ps)

        # Update classes if provided
        if class_ids is not None:
            existing_cls = (
                await db.execute(
                    select(ProjectClass).where(ProjectClass.project_id == project_id)
                )
            ).scalars().all()
            for pc in existing_cls:
                await db.delete(pc)

            for class_id in class_ids:
                pc = ProjectClass(project_id=project_id, class_id=class_id)
                db.add(pc)

        db.add(project)
        await db.flush()
        await db.refresh(project)
        return project

    @staticmethod
    async def _transition_status(
        db: AsyncSession, project_id: str, transition_to: str
    ) -> Project:
        """Internal helper to perform a state transition."""
        project = await ProjectService.get_project(db, project_id)

        current = project.status
        expected_next = PROJECT_TRANSITIONS.get(current)
        if expected_next != transition_to:
            raise InvalidStateTransitionException(
                f"项目状态不能从 '{current}' 转换到 '{transition_to}'"
            )

        project.status = transition_to
        db.add(project)
        await db.flush()
        await db.refresh(project)
        return project

    @staticmethod
    async def activate_project(db: AsyncSession, project_id: str) -> Project:
        """Transition project from draft to active."""
        return await ProjectService._transition_status(db, project_id, "active")

    @staticmethod
    async def complete_project(db: AsyncSession, project_id: str) -> Project:
        """Transition project from active to completed."""
        return await ProjectService._transition_status(db, project_id, "completed")

    @staticmethod
    async def archive_project(db: AsyncSession, project_id: str) -> Project:
        """Transition project from completed to archived."""
        return await ProjectService._transition_status(db, project_id, "archived")


def _format_project_item(project: Project) -> dict:
    """Format a project model instance into a response dict."""
    subjects_data = []
    if hasattr(project, "subjects") and project.subjects:
        for ps in project.subjects:
            if ps.subject:
                subjects_data.append({
                    "id": ps.subject.id,
                    "name": ps.subject.name,
                })

    classes_data = []
    if hasattr(project, "classes") and project.classes:
        for pc in project.classes:
            if pc.target_class:
                classes_data.append({
                    "id": pc.target_class.id,
                    "name": pc.target_class.name,
                    "grade": pc.target_class.grade,
                })

    return {
        "id": project.id,
        "school_id": project.school_id,
        "name": project.name,
        "grade": project.grade,
        "driving_question": project.driving_question,
        "objectives": project.objectives or [],
        "lesson_count": project.lesson_count,
        "status": project.status,
        "owner_id": project.owner_id,
        "owner_name": project.owner.name if project.owner else None,
        "subjects": subjects_data,
        "classes": classes_data,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }
