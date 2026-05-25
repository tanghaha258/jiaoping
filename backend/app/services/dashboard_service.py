"""Dashboard service: aggregate statistics for the admin/teacher dashboard."""

import logging
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.school import School
from app.models.project import Project
from app.models.task import Task
from app.models.resource import Resource
from app.models.ai_agent_call import AIAgentCall

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for dashboard aggregate statistics."""

    @staticmethod
    async def get_overview(
        db: AsyncSession,
        school_id: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> dict:
        """Return aggregate counts for the dashboard overview.

        Args:
            db: Database session.
            school_id: If provided, scope all queries to this school.
            owner_id: If provided (teacher scope), scope project/task stats to this owner's projects.

        Returns:
            dict with counts for schools, teachers, students, projects, tasks, resources, ai_calls.
        """
        # --- Schools count (always global, not scoped) ---
        school_count_query = select(func.count()).select_from(School)
        school_count = (await db.execute(school_count_query)).scalar()

        # --- Teachers count ---
        teacher_count_query = select(func.count()).select_from(User).where(User.role == "teacher")
        if school_id:
            teacher_count_query = teacher_count_query.where(User.school_id == school_id)
        teacher_count = (await db.execute(teacher_count_query)).scalar()

        # --- Students count ---
        student_count_query = select(func.count()).select_from(User).where(User.role == "student")
        if school_id:
            student_count_query = student_count_query.where(User.school_id == school_id)
        student_count = (await db.execute(student_count_query)).scalar()

        # --- Projects count ---
        project_count_query = select(func.count()).select_from(Project)
        if school_id:
            project_count_query = project_count_query.where(Project.school_id == school_id)
        if owner_id:
            project_count_query = project_count_query.where(Project.owner_id == owner_id)
        project_count = (await db.execute(project_count_query)).scalar()

        # --- Tasks count ---
        task_count_query = select(func.count()).select_from(Task)
        if school_id or owner_id:
            task_count_query = task_count_query.join(Project, Task.project_id == Project.id)
        if school_id:
            task_count_query = task_count_query.where(Project.school_id == school_id)
        if owner_id:
            task_count_query = task_count_query.where(Project.owner_id == owner_id)
        task_count = (await db.execute(task_count_query)).scalar()

        # --- Resources count ---
        resource_count_query = select(func.count()).select_from(Resource)
        if school_id:
            resource_count_query = resource_count_query.where(Resource.school_id == school_id)
        resource_count = (await db.execute(resource_count_query)).scalar()

        # --- AI calls count ---
        ai_call_count_query = select(func.count()).select_from(AIAgentCall)
        if school_id:
            ai_call_count_query = ai_call_count_query.where(AIAgentCall.school_id == school_id)
        if owner_id:
            ai_call_count_query = ai_call_count_query.where(AIAgentCall.user_id == owner_id)
        ai_call_count = (await db.execute(ai_call_count_query)).scalar()

        return {
            "schools": school_count,
            "teachers": teacher_count,
            "students": student_count,
            "projects": project_count,
            "tasks": task_count,
            "resources": resource_count,
            "ai_calls": ai_call_count,
        }

    @staticmethod
    async def get_ai_usage(
        db: AsyncSession,
        school_id: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> dict:
        """Return AI usage breakdown: call counts by scenario and by provider.

        Args:
            db: Database session.
            school_id: If provided, scope to this school.
            owner_id: If provided (teacher scope), scope to this user's AI calls.

        Returns:
            dict with by_scenario list, by_provider list, total_calls.
        """
        # --- By scenario ---
        by_scenario_query = (
            select(AIAgentCall.scenario, func.count().label("count"))
            .select_from(AIAgentCall)
            .group_by(AIAgentCall.scenario)
            .order_by(func.count().desc())
        )
        if school_id:
            by_scenario_query = by_scenario_query.where(AIAgentCall.school_id == school_id)
        if owner_id:
            by_scenario_query = by_scenario_query.where(AIAgentCall.user_id == owner_id)
        by_scenario_result = await db.execute(by_scenario_query)
        by_scenario = [
            {"scenario": row.scenario, "count": row.count}
            for row in by_scenario_result
        ]

        # --- By provider ---
        by_provider_query = (
            select(AIAgentCall.provider, func.count().label("count"))
            .select_from(AIAgentCall)
            .group_by(AIAgentCall.provider)
            .order_by(func.count().desc())
        )
        if school_id:
            by_provider_query = by_provider_query.where(AIAgentCall.school_id == school_id)
        if owner_id:
            by_provider_query = by_provider_query.where(AIAgentCall.user_id == owner_id)
        by_provider_result = await db.execute(by_provider_query)
        by_provider = [
            {"provider": row.provider, "count": row.count}
            for row in by_provider_result
        ]

        # --- Total ---
        total_query = select(func.count()).select_from(AIAgentCall)
        if school_id:
            total_query = total_query.where(AIAgentCall.school_id == school_id)
        if owner_id:
            total_query = total_query.where(AIAgentCall.user_id == owner_id)
        total_calls = (await db.execute(total_query)).scalar()

        return {
            "by_scenario": by_scenario,
            "by_provider": by_provider,
            "total_calls": total_calls,
        }

    @staticmethod
    async def get_project_trends(
        db: AsyncSession,
        school_id: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> dict:
        """Return project trends: counts by month and by status.

        Args:
            db: Database session.
            school_id: If provided, scope to this school.
            owner_id: If provided (teacher scope), scope to this owner's projects.

        Returns:
            dict with by_month list and by_status list.
        """
        # --- By status ---
        by_status_query = (
            select(Project.status, func.count().label("count"))
            .select_from(Project)
            .group_by(Project.status)
        )
        if school_id:
            by_status_query = by_status_query.where(Project.school_id == school_id)
        if owner_id:
            by_status_query = by_status_query.where(Project.owner_id == owner_id)
        by_status_result = await db.execute(by_status_query)
        by_status = [
            {"status": row.status, "count": row.count}
            for row in by_status_result
        ]

        # --- By month ---
        # Group by year and month from created_at
        by_month_query = (
            select(
                func.strftime("%Y-%m", Project.created_at).label("month"),
                func.count().label("count"),
            )
            .select_from(Project)
            .group_by(func.strftime("%Y-%m", Project.created_at))
            .order_by("month")
        )
        if school_id:
            by_month_query = by_month_query.where(Project.school_id == school_id)
        if owner_id:
            by_month_query = by_month_query.where(Project.owner_id == owner_id)
        by_month_result = await db.execute(by_month_query)
        by_month = [
            {"month": row.month, "count": row.count}
            for row in by_month_result
        ]

        return {
            "by_month": by_month,
            "by_status": by_status,
        }
