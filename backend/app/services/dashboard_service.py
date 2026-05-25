"""Dashboard service: aggregate statistics for the admin/teacher dashboard."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ai_agent import AIAgent
from app.models.user import User
from app.models.school import School
from app.models.class_ import Class
from app.models.subject import Subject
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

    @staticmethod
    async def get_trial_readiness(db: AsyncSession) -> dict:
        """Return the admin-facing checklist for trial operation."""
        counts = {
            "active_schools": await DashboardService._count(
                db,
                School,
                School.status == "active",
                School.deleted_at.is_(None),
            ),
            "classes": await DashboardService._count(db, Class, Class.deleted_at.is_(None)),
            "subjects": await DashboardService._count(db, Subject, Subject.deleted_at.is_(None)),
            "teachers": await DashboardService._count(
                db,
                User,
                User.role == "teacher",
                User.status == "active",
                User.deleted_at.is_(None),
            ),
            "students": await DashboardService._count(
                db,
                User,
                User.role == "student",
                User.status == "active",
                User.deleted_at.is_(None),
            ),
            "lesson_plan_agents": await DashboardService._count(
                db,
                AIAgent,
                AIAgent.scenario == "lesson_plan",
                AIAgent.enabled.is_(True),
                AIAgent.deleted_at.is_(None),
            ),
            "workflow_projects": await DashboardService._count(
                db,
                Project,
                Project.status.in_(["active", "completed"]),
                Project.deleted_at.is_(None),
            ),
            "student_tasks": await DashboardService._count(
                db,
                Task,
                Task.status.in_(["published", "closed"]),
                Task.deleted_at.is_(None),
            ),
            "resources": await DashboardService._count(
                db,
                Resource,
                Resource.status.in_(["active", "published"]),
                Resource.deleted_at.is_(None),
            ),
        }

        items = [
            DashboardService._service_readiness_item(),
            DashboardService._organization_data_item(counts),
            DashboardService._user_accounts_item(counts),
            DashboardService._ai_contract_item(counts),
            DashboardService._teaching_workflow_item(counts),
            DashboardService._student_task_item(counts),
            DashboardService._resources_item(counts),
            DashboardService._backup_path_item(),
        ]
        summary = {
            "ok": sum(1 for item in items if item["status"] == "ok"),
            "warning": sum(1 for item in items if item["status"] == "warning"),
            "error": sum(1 for item in items if item["status"] == "error"),
        }

        return {
            "status": "action_required" if summary["error"] else "ready",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "items": items,
        }

    @staticmethod
    async def _count(db: AsyncSession, model, *conditions) -> int:
        stmt = select(func.count()).select_from(model)
        for condition in conditions:
            stmt = stmt.where(condition)
        return int((await db.execute(stmt)).scalar() or 0)

    @staticmethod
    def _item(
        key: str,
        label: str,
        status: str,
        description: str,
        metric: str,
        action: str,
        route: str,
    ) -> dict:
        return {
            "key": key,
            "label": label,
            "status": status,
            "description": description,
            "metric": metric,
            "action": action,
            "route": route,
        }

    @staticmethod
    def _service_readiness_item() -> dict:
        provider_mode = "gjt_api" if all([
            settings.GJT_API_BASE_URL,
            settings.GJT_API_KEY,
            settings.GJT_AGENT_ID,
        ]) else "mock"
        try:
            upload_dir = Path(settings.UPLOAD_DIR).resolve()
            upload_dir.mkdir(parents=True, exist_ok=True)
            status = "ok"
            description = "API、数据库会话和上传目录可用，AI Provider 当前按配置运行。"
        except Exception as exc:  # pragma: no cover - only exercised by broken deployments
            upload_dir = Path(settings.UPLOAD_DIR)
            status = "error"
            description = f"上传目录不可用：{exc}"

        return DashboardService._item(
            key="service_readiness",
            label="服务运行状态",
            status=status,
            description=description,
            metric=f"AI Provider: {provider_mode} / 上传目录: {upload_dir}",
            action="查看健康检查接口",
            route="/admin/settings",
        )

    @staticmethod
    def _organization_data_item(counts: dict) -> dict:
        ready = counts["active_schools"] > 0 and counts["classes"] > 0 and counts["subjects"] > 0
        return DashboardService._item(
            key="organization_data",
            label="基础组织数据",
            status="ok" if ready else "error",
            description="学校、班级和学科是项目、账号和教学任务运转的基础。",
            metric=f"学校 {counts['active_schools']} / 班级 {counts['classes']} / 学科 {counts['subjects']}",
            action="导入或维护学校、班级、学科",
            route="/admin/schools",
        )

    @staticmethod
    def _user_accounts_item(counts: dict) -> dict:
        ready = counts["teachers"] > 0 and counts["students"] > 0
        return DashboardService._item(
            key="user_accounts",
            label="教师与学生账号",
            status="ok" if ready else "error",
            description="试运行至少需要可登录的教师账号和学生账号。",
            metric=f"教师 {counts['teachers']} / 学生 {counts['students']}",
            action="导入或创建试运行账号",
            route="/admin/users",
        )

    @staticmethod
    def _ai_contract_item(counts: dict) -> dict:
        ready = counts["lesson_plan_agents"] > 0
        return DashboardService._item(
            key="ai_contract",
            label="AI 智能体契约",
            status="ok" if ready else "error",
            description="教学方案生成需要启用的 lesson_plan 智能体配置。",
            metric=f"可用教学方案智能体 {counts['lesson_plan_agents']}",
            action="检查 AI 智能体配置",
            route="/admin/ai-agents",
        )

    @staticmethod
    def _teaching_workflow_item(counts: dict) -> dict:
        ready = counts["workflow_projects"] > 0
        return DashboardService._item(
            key="teaching_workflow",
            label="教学项目闭环",
            status="ok" if ready else "warning",
            description="已有激活或完成项目时，可以直接演示教学评主流程。",
            metric=f"激活/完成项目 {counts['workflow_projects']}",
            action="让教师创建或采纳一个教学项目",
            route="/teacher/projects",
        )

    @staticmethod
    def _student_task_item(counts: dict) -> dict:
        ready = counts["student_tasks"] > 0
        return DashboardService._item(
            key="student_task_availability",
            label="学生任务可见性",
            status="ok" if ready else "warning",
            description="发布任务后学生端才能看到任务并提交成果。",
            metric=f"已发布/已关闭任务 {counts['student_tasks']}",
            action="进入项目详情发布任务",
            route="/teacher/projects",
        )

    @staticmethod
    def _resources_item(counts: dict) -> dict:
        ready = counts["resources"] > 0
        return DashboardService._item(
            key="resources",
            label="资源中心",
            status="ok" if ready else "warning",
            description="资源中心有内容时，教学设计和任务支撑更完整。",
            metric=f"可用资源 {counts['resources']}",
            action="导入或维护校本资源",
            route="/teacher/resources",
        )

    @staticmethod
    def _backup_path_item() -> dict:
        db_path = DashboardService._sqlite_database_path()
        if db_path is None:
            return DashboardService._item(
                key="backup_path",
                label="数据备份路径",
                status="warning",
                description="当前不是 SQLite 数据库，请使用对应数据库的原生命令做备份。",
                metric="非 SQLite 数据库",
                action="查看部署文档中的备份建议",
                route="/admin/settings",
            )

        exists = db_path.exists()
        return DashboardService._item(
            key="backup_path",
            label="数据备份路径",
            status="ok" if exists else "warning",
            description="SQLite 试运行可使用脚本进行时间戳备份和安全恢复。",
            metric=str(db_path),
            action="执行 scripts/backup-sqlite.ps1",
            route="/admin/settings",
        )

    @staticmethod
    def _sqlite_database_path() -> Optional[Path]:
        database_url = settings.DATABASE_URL
        if not database_url.startswith("sqlite"):
            return None
        marker = ":///"
        if marker not in database_url:
            return None
        raw_path = database_url.split(marker, 1)[1]
        if raw_path in {":memory:", ""}:
            return None
        path = Path(raw_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        return path.resolve()
