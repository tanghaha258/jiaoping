"""Dashboard service: aggregate statistics for the admin/teacher dashboard."""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.ai_agent import AIAgent
from app.models.user import User
from app.models.school import School
from app.models.class_ import Class
from app.models.subject import Subject
from app.models.project import Project
from app.models.task import Task
from app.models.resource import Resource
from app.models.ai_agent_call import AIAgentCall
from app.services.audit_service import create_audit_log

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for dashboard aggregate statistics."""

    TRIAL_RUNBOOK_STAGE_KEYS = {
        "service_readiness",
        "base_data",
        "account_access",
        "ai_provider_rehearsal",
        "teaching_workflow",
        "resource_and_backup",
    }
    TRIAL_RUNBOOK_RECORD_ACTION = "trial_runbook.record"
    TRIAL_RUNBOOK_RECORD_TARGET_TYPE = "trial_runbook_stage"
    TRIAL_DELIVERY_DEMO_SCRIPT = [
        {
            "step": 1,
            "role": "system_admin",
            "title": "管理员打开试点交付包",
            "route": "/admin/trial-delivery",
            "expected_evidence": "能看到现场验收清单、演示脚本、测试账号交付和下载材料。",
        },
        {
            "step": 2,
            "role": "teacher",
            "title": "教师打开跨学科项目",
            "route": "/teacher/projects",
            "expected_evidence": "能看到项目列表、项目详情和课时任务入口。",
        },
        {
            "step": 3,
            "role": "teacher",
            "title": "教师进入 AI 教学方案",
            "route": "/teacher/ai/lesson-plan",
            "expected_evidence": "能生成或查看待审阅的 AI 教学方案草案，并保持教师采纳门槛。",
        },
        {
            "step": 4,
            "role": "student",
            "title": "学生查看学习任务",
            "route": "/student/tasks",
            "expected_evidence": "能看到已发布任务并进入任务详情。",
        },
        {
            "step": 5,
            "role": "teacher",
            "title": "教师审阅提交并确认评价",
            "route": "/teacher/evaluations",
            "expected_evidence": "能查看评价记录，确认后的反馈对学生可见。",
        },
        {
            "step": 6,
            "role": "system_admin",
            "title": "管理员核验 AI 调用和审计证据",
            "route": "/admin/ai-calls",
            "expected_evidence": "能查看 AI 调用观测、失败诊断和调用台账。",
        },
    ]
    TRIAL_DELIVERY_ACCOUNTS = [
        {
            "role": "system_admin",
            "username": "admin",
            "password_hint": "见本地账号交付清单；正式试点前必须重置。",
            "purpose": "查看交付包、readiness、AI Provider、审计日志和系统设置。",
        },
        {
            "role": "school_admin",
            "username": "schooladmin",
            "password_hint": "见本地账号交付清单；正式试点前必须重置。",
            "purpose": "核对学校、班级、教师学生账号和试运行演练记录。",
        },
        {
            "role": "teacher",
            "username": "teacher001",
            "password_hint": "见本地账号交付清单；正式试点前必须重置。",
            "purpose": "演示项目、任务、AI 教学方案、提交审阅和评价确认。",
        },
        {
            "role": "student",
            "username": "student001",
            "password_hint": "见本地账号交付清单；正式试点前必须重置。",
            "purpose": "演示学习任务查看、作品提交和反馈查看。",
        },
    ]
    TRIAL_DELIVERY_PRINTABLE_ACCEPTANCE = {
        "title": "现场验收确认单",
        "purpose": "确认试点现场能够演示教学评一体化闭环、AI 使用证据、安全权限边界和交付材料完整性。",
        "required_signoffs": ["平台管理员", "学校管理员", "试点教师"],
        "statements": [
            "已确认服务、数据库、上传目录和备份路径可用。",
            "已确认教师、学生、学校管理员账号可登录，并已准备独立的密码发放清单。",
            "已确认 AI 输出需经教师审核采纳后进入业务闭环。",
            "已确认本交付材料不包含密码哈希、API Key、JWT Secret 或 Provider 密钥。",
        ],
    }
    TRIAL_DELIVERY_FALLBACK_PROCEDURES = [
        {
            "key": "network_unavailable",
            "title": "现场网络不可用",
            "trigger": "前端页面或后端健康检查无法访问。",
            "owner": "平台管理员",
            "steps": [
                "优先使用本机演示环境访问 http://127.0.0.1:3000。",
                "确认后端健康检查 http://127.0.0.1:8000/api/v1/health 是否可用。",
                "如外网不可用，使用已下载的 Markdown/JSON 交付材料完成讲解。",
            ],
            "evidence": ["本机服务健康检查截图", "离线交付包 Markdown/JSON 文件"],
        },
        {
            "key": "provider_unavailable",
            "title": "AI Provider 不可用",
            "trigger": "真实 Provider 配置缺失、超时或返回失败。",
            "owner": "平台管理员",
            "steps": [
                "在 AI 智能体治理页执行配置自检。",
                "保留 Mock 或人工回填模式完成教学方案演示。",
                "在 AI 调用观测页展示失败类别、补救建议和审计记录。",
            ],
            "evidence": ["Provider 配置自检结果", "AI 调用失败诊断记录", "Mock/人工回填演示记录"],
        },
        {
            "key": "account_access_issue",
            "title": "账号无法登录",
            "trigger": "教师、学生或学校管理员无法使用试点账号进入对应页面。",
            "owner": "学校管理员",
            "steps": [
                "在用户管理页核对账号状态、角色和所属学校/班级。",
                "由系统管理员执行密码重置并重新发放临时密码。",
                "记录重置操作，正式试点前再次要求用户修改密码。",
            ],
            "evidence": ["用户管理账号状态", "密码重置审计记录", "重新登录截图"],
        },
        {
            "key": "backup_restore",
            "title": "数据备份或恢复演练",
            "trigger": "试点前需要确认 SQLite 数据和 uploads 目录可恢复。",
            "owner": "平台管理员",
            "steps": [
                "执行 SQLite 备份脚本并保存时间戳文件。",
                "恢复前生成安全备份，避免覆盖当前演示数据。",
                "恢复后重新访问 readiness 和交付包页面确认数据可读。",
            ],
            "evidence": ["备份文件路径", "恢复前安全备份路径", "恢复后 readiness 截图"],
        },
    ]
    TRIAL_DELIVERY_ROLE_HANDOFFS = [
        {
            "role": "platform_admin",
            "title": "平台管理员交接卡",
            "route": "/admin/trial-delivery",
            "checklist": ["下载交付材料", "核对 readiness", "确认 AI Provider 状态", "保存备份路径"],
            "handoff_note": "负责现场技术状态、Provider 兜底、备份恢复和最终交付材料归档。",
        },
        {
            "role": "school_admin",
            "title": "学校管理员交接卡",
            "route": "/admin/users",
            "checklist": ["核对学校班级", "核对教师学生账号", "保管初始密码发放清单"],
            "handoff_note": "负责试点学校组织数据、账号发放和现场账号问题协调。",
        },
        {
            "role": "teacher",
            "title": "试点教师交接卡",
            "route": "/teacher/projects",
            "checklist": ["打开跨学科项目", "演示 AI 教学方案", "发布任务并确认评价"],
            "handoff_note": "负责展示教学设计、学习任务、评价反馈和教师采纳 AI 的边界。",
        },
        {
            "role": "student",
            "title": "学生体验交接卡",
            "route": "/student/tasks",
            "checklist": ["查看已发布任务", "提交学习成果", "查看教师确认后的反馈"],
            "handoff_note": "负责展示学生端任务参与、成果提交和反馈查看。",
        },
        {
            "role": "reviewer",
            "title": "评委验收交接卡",
            "route": "/admin/ai-calls",
            "checklist": ["查看完整演示脚本", "核对 AI 使用证据", "核对权限和审计边界"],
            "handoff_note": "聚焦教学闭环、AI 证据、安全合规和可推广材料。",
        },
    ]

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
            await DashboardService._ai_contract_item(db, counts),
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
    async def get_trial_operations_runbook(db: AsyncSession) -> dict:
        """Return ordered trial rehearsal stages derived from readiness evidence."""
        readiness = await DashboardService.get_trial_readiness(db)
        items = {item["key"]: item for item in readiness["items"]}
        stages = [
            DashboardService._runbook_stage(
                key="service_readiness",
                title="服务与数据可用",
                owner="平台管理员",
                items=[items.get("service_readiness")],
                route="/admin",
                primary_action="查看 readiness",
                next_step="确认本地服务、数据库和上传目录可用后，进入基础数据检查。",
            ),
            DashboardService._runbook_stage(
                key="base_data",
                title="基础数据演练",
                owner="区县/学校管理员",
                items=[items.get("organization_data")],
                route="/admin/schools",
                primary_action="核对学校班级学科",
                next_step="学校、班级和学科齐备后，继续核对试点账号。",
            ),
            DashboardService._runbook_stage(
                key="account_access",
                title="账号登录演练",
                owner="学校管理员",
                items=[items.get("user_accounts")],
                route="/admin/users",
                primary_action="核对教师学生账号",
                next_step="确认教师和学生账号可以登录，并准备初始密码发放清单。",
            ),
            DashboardService._ai_provider_runbook_stage(items.get("ai_contract")),
            DashboardService._runbook_stage(
                key="teaching_workflow",
                title="教学闭环演练",
                owner="试点教师",
                items=[items.get("teaching_workflow"), items.get("student_task_availability")],
                route="/teacher/projects",
                primary_action="演练项目到任务闭环",
                next_step="确认教师可创建或采纳项目，学生端可看到已发布任务。",
            ),
            DashboardService._resource_backup_runbook_stage(
                items.get("resources"),
                items.get("backup_path"),
            ),
        ]
        summary = {
            "ok": sum(1 for stage in stages if stage["status"] == "ok"),
            "warning": sum(1 for stage in stages if stage["status"] == "warning"),
            "error": sum(1 for stage in stages if stage["status"] == "error"),
        }
        return {
            "status": "action_required" if summary["error"] else "ready",
            "checked_at": readiness["checked_at"],
            "summary": summary,
            "stages": stages,
        }

    @staticmethod
    async def create_trial_runbook_record(
        db: AsyncSession,
        user: User,
        stage_key: str,
        payload,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        """Append one trial runbook rehearsal evidence record."""
        DashboardService._validate_trial_runbook_stage(stage_key)
        detail = {
            "stage_key": stage_key,
            "status": payload.status,
            "note": payload.note.strip(),
            "evidence": DashboardService._normalize_record_evidence(payload.evidence),
        }
        log = await create_audit_log(
            db=db,
            user_id=user.id,
            action=DashboardService.TRIAL_RUNBOOK_RECORD_ACTION,
            target_type=DashboardService.TRIAL_RUNBOOK_RECORD_TARGET_TYPE,
            target_id=stage_key,
            ip=ip,
            user_agent=user_agent,
            detail=detail,
        )
        if log is None:
            raise RuntimeError("Failed to save trial runbook record")
        log.user = user
        return DashboardService._trial_runbook_record_to_dict(log)

    @staticmethod
    async def list_trial_runbook_records(
        db: AsyncSession,
        user: User,
        stage_key: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict:
        """List recent trial runbook rehearsal evidence records."""
        if stage_key:
            DashboardService._validate_trial_runbook_stage(stage_key)

        query = (
            select(AuditLog)
            .options(joinedload(AuditLog.user))
            .where(AuditLog.action == DashboardService.TRIAL_RUNBOOK_RECORD_ACTION)
            .where(AuditLog.target_type == DashboardService.TRIAL_RUNBOOK_RECORD_TARGET_TYPE)
        )
        count_query = (
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.action == DashboardService.TRIAL_RUNBOOK_RECORD_ACTION)
            .where(AuditLog.target_type == DashboardService.TRIAL_RUNBOOK_RECORD_TARGET_TYPE)
        )

        if stage_key:
            query = query.where(AuditLog.target_id == stage_key)
            count_query = count_query.where(AuditLog.target_id == stage_key)

        if user.role == "school_admin" and user.school_id:
            query = query.join(User, AuditLog.user_id == User.id).where(
                User.school_id == user.school_id
            )
            count_query = count_query.join(User, AuditLog.user_id == User.id).where(
                User.school_id == user.school_id
            )

        total = (await db.execute(count_query)).scalar() or 0
        offset = (page - 1) * page_size
        result = await db.execute(
            query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)
        )
        logs = result.unique().scalars().all()
        return {
            "items": [DashboardService._trial_runbook_record_to_dict(log) for log in logs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }

    @staticmethod
    async def get_trial_delivery_package(db: AsyncSession, user: User) -> dict:
        """Build a read-only handover package from readiness and rehearsal evidence."""
        readiness = await DashboardService.get_trial_readiness(db)
        runbook = await DashboardService.get_trial_operations_runbook(db)
        records = await DashboardService.list_trial_runbook_records(
            db=db,
            user=user,
            page=1,
            page_size=50,
        )
        latest_by_stage = DashboardService._latest_runbook_records_by_stage(records["items"])
        checklist = [
            DashboardService._trial_delivery_checklist_item(
                stage,
                latest_by_stage.get(stage["key"]),
            )
            for stage in runbook["stages"]
        ]
        record_summary = DashboardService._trial_delivery_record_summary(records["items"])
        summary = {
            "readiness_ok": readiness["summary"]["ok"],
            "readiness_warning": readiness["summary"]["warning"],
            "readiness_error": readiness["summary"]["error"],
            **record_summary,
        }
        package = {
            "status": DashboardService._trial_delivery_status(readiness, checklist),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "audience_sections": DashboardService._trial_delivery_audience_sections(),
            "acceptance_checklist": checklist,
            "demo_script": DashboardService.TRIAL_DELIVERY_DEMO_SCRIPT,
            "accounts": DashboardService.TRIAL_DELIVERY_ACCOUNTS,
            "printable_acceptance": DashboardService.TRIAL_DELIVERY_PRINTABLE_ACCEPTANCE,
            "fallback_procedures": DashboardService.TRIAL_DELIVERY_FALLBACK_PROCEDURES,
            "role_handoffs": DashboardService.TRIAL_DELIVERY_ROLE_HANDOFFS,
        }
        package["materials"] = {
            "markdown": DashboardService._trial_delivery_markdown(package),
            "json": json.dumps(package, ensure_ascii=False, indent=2),
        }
        return package

    @staticmethod
    def _latest_runbook_records_by_stage(records: list[dict]) -> dict[str, dict]:
        latest: dict[str, dict] = {}
        for record in records:
            stage_key = record.get("stage_key")
            if stage_key and stage_key not in latest:
                latest[stage_key] = record
        return latest

    @staticmethod
    def _trial_delivery_record_summary(records: list[dict]) -> dict:
        return {
            "runbook_checked": sum(1 for record in records if record.get("status") == "checked"),
            "runbook_blocked": sum(1 for record in records if record.get("status") == "blocked"),
            "runbook_skipped": sum(1 for record in records if record.get("status") == "skipped"),
        }

    @staticmethod
    def _trial_delivery_checklist_item(stage: dict, latest_record: Optional[dict]) -> dict:
        return {
            "key": stage["key"],
            "title": stage["title"],
            "status": stage["status"],
            "route": stage["route"],
            "owner": stage["owner"],
            "primary_action": stage["primary_action"],
            "evidence": stage["evidence"],
            "next_step": stage["next_step"],
            "latest_record": latest_record,
        }

    @staticmethod
    def _trial_delivery_status(readiness: dict, checklist: list[dict]) -> str:
        if readiness["summary"]["error"]:
            return "action_required"
        if any(item["status"] == "error" for item in checklist):
            return "action_required"
        if any((item.get("latest_record") or {}).get("status") == "blocked" for item in checklist):
            return "action_required"
        return "ready"

    @staticmethod
    def _trial_delivery_audience_sections() -> list[dict]:
        return [
            {
                "key": "operator",
                "title": "平台管理员交付要点",
                "items": ["检查 readiness", "下载交付材料", "核对 AI Provider 和审计证据"],
            },
            {
                "key": "school_admin",
                "title": "学校管理员交付要点",
                "items": ["确认组织数据", "核对教师与学生账号", "保存初始密码发放清单"],
            },
            {
                "key": "reviewer",
                "title": "评委验收要点",
                "items": ["查看完整教学闭环", "查看 AI 使用证据", "查看安全和权限边界"],
            },
        ]

    @staticmethod
    def _trial_delivery_markdown(package: dict) -> str:
        lines = [
            "# 试点交付包",
            "",
            f"- 生成时间：{package['generated_at']}",
            f"- 状态：{'可交付' if package['status'] == 'ready' else '需要处理'}",
            f"- readiness：正常 {package['summary']['readiness_ok']} / 提醒 {package['summary']['readiness_warning']} / 阻断 {package['summary']['readiness_error']}",
            f"- 演练记录：已检查 {package['summary']['runbook_checked']} / 阻断 {package['summary']['runbook_blocked']} / 已跳过 {package['summary']['runbook_skipped']}",
            "",
            "## 现场验收清单",
            "",
        ]
        for item in package["acceptance_checklist"]:
            latest = item.get("latest_record")
            latest_text = "尚无演练记录"
            if latest:
                latest_text = (
                    f"{latest.get('status')} / "
                    f"{latest.get('operator_name') or '管理员'} / "
                    f"{latest.get('note') or '未填写备注'}"
                )
            lines.extend([
                f"### {item['title']}",
                f"- 状态：{DashboardService._status_label(item['status'])}",
                f"- 责任角色：{item['owner']}",
                f"- 处理入口：{item['route']}",
                f"- 最新演练：{latest_text}",
                "- 证据：",
            ])
            for evidence in item["evidence"]:
                lines.append(f"  - {evidence}")
            if latest and latest.get("evidence"):
                lines.append("- 演练补充证据：")
                for evidence in latest["evidence"]:
                    lines.append(f"  - {evidence}")
            lines.append("")

        lines.extend(["## 演示脚本", ""])
        for step in package["demo_script"]:
            lines.append(
                f"{step['step']}. [{step['role']}] {step['title']}："
                f"{step['route']}；验收证据：{step['expected_evidence']}"
            )

        lines.extend(["", "## 测试账号交付", ""])
        for account in package["accounts"]:
            lines.append(
                f"- {account['role']} / {account['username']}："
                f"{account['purpose']}（{account['password_hint']}）"
            )

        printable = package["printable_acceptance"]
        lines.extend(["", "## 打印验收说明", ""])
        lines.append(f"### {printable['title']}")
        lines.append(f"- 用途：{printable['purpose']}")
        lines.append(f"- 需确认角色：{'、'.join(printable['required_signoffs'])}")
        lines.append("- 确认事项：")
        for statement in printable["statements"]:
            lines.append(f"  - {statement}")

        lines.extend(["", "## 异常处置流程", ""])
        for procedure in package["fallback_procedures"]:
            lines.extend([
                f"### {procedure['title']}",
                f"- 触发条件：{procedure['trigger']}",
                f"- 责任角色：{procedure['owner']}",
                "- 处理步骤：",
            ])
            for step in procedure["steps"]:
                lines.append(f"  - {step}")
            lines.append("- 留存证据：")
            for evidence in procedure["evidence"]:
                lines.append(f"  - {evidence}")
            lines.append("")

        lines.extend(["## 分角色交接卡", ""])
        for handoff in package["role_handoffs"]:
            lines.extend([
                f"### {handoff['title']}",
                f"- 入口：{handoff['route']}",
                f"- 交接说明：{handoff['handoff_note']}",
                "- 核对项：",
            ])
            for item in handoff["checklist"]:
                lines.append(f"  - {item}")
            lines.append("")

        lines.extend([
            "",
            "## 交付提醒",
            "",
            "- 本材料不包含密码哈希、API Key、JWT Secret 或 Provider 密钥。",
            "- 正式试点前必须完成测试账号密码重置。",
        ])
        return "\n".join(lines)

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
    def _runbook_stage(
        key: str,
        title: str,
        owner: str,
        items: list[Optional[dict]],
        route: str,
        primary_action: str,
        next_step: str,
    ) -> dict:
        present_items = [item for item in items if item]
        return {
            "key": key,
            "title": title,
            "status": DashboardService._worst_status(present_items),
            "owner": owner,
            "route": route,
            "primary_action": primary_action,
            "evidence": DashboardService._stage_evidence(present_items),
            "next_step": next_step,
        }

    @staticmethod
    def _worst_status(items: list[dict]) -> str:
        order = {"ok": 0, "warning": 1, "error": 2}
        if not items:
            return "warning"
        return max((item["status"] for item in items), key=lambda status: order.get(status, 1))

    @staticmethod
    def _stage_evidence(items: list[dict]) -> list[str]:
        if not items:
            return ["暂无 readiness 证据"]
        return [
            f"{item['label']}：{item['metric']}（{DashboardService._status_label(item['status'])}）"
            for item in items
        ]

    @staticmethod
    def _status_label(status: str) -> str:
        if status == "ok":
            return "正常"
        if status == "warning":
            return "提醒"
        return "阻断"

    @staticmethod
    def _validate_trial_runbook_stage(stage_key: str) -> None:
        if stage_key not in DashboardService.TRIAL_RUNBOOK_STAGE_KEYS:
            raise ValueError("Unknown trial operations stage")

    @staticmethod
    def _normalize_record_evidence(evidence: list[str]) -> list[str]:
        normalized = []
        for item in evidence[:8]:
            text = str(item).strip()
            if text:
                normalized.append(text[:300])
        return normalized

    @staticmethod
    def _trial_runbook_record_to_dict(log: AuditLog) -> dict:
        detail = log.detail or {}
        return {
            "id": log.id,
            "stage_key": detail.get("stage_key") or log.target_id,
            "status": detail.get("status"),
            "note": detail.get("note") or "",
            "evidence": detail.get("evidence") or [],
            "operator_id": log.user_id,
            "operator_name": log.user.name if log.user else None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }

    @staticmethod
    def _ai_provider_runbook_stage(ai_item: Optional[dict]) -> dict:
        route = "/admin/ai-agents"
        action = "执行 Provider 配置自检"
        next_step = "保持 mock/manual 可演练；真实 Provider 接入前先完成配置自检，再查看失败诊断。"
        if ai_item and ai_item.get("route") == "/admin/ai-calls":
            route = "/admin/ai-calls"
            action = "查看 AI 调用诊断"
            next_step = "先处理近期真实 Provider 调用失败，再继续教师侧生成演练。"
        return DashboardService._runbook_stage(
            key="ai_provider_rehearsal",
            title="AI Provider演练",
            owner="平台管理员",
            items=[ai_item],
            route=route,
            primary_action=action,
            next_step=next_step,
        )

    @staticmethod
    def _resource_backup_runbook_stage(resource_item: Optional[dict], backup_item: Optional[dict]) -> dict:
        route = "/teacher/resources" if resource_item and resource_item.get("status") != "ok" else "/admin"
        action = "补齐资源或执行备份"
        if backup_item and backup_item.get("status") != "ok":
            route = "/admin"
            action = "核对备份路径"
        return DashboardService._runbook_stage(
            key="resource_and_backup",
            title="资源与备份演练",
            owner="平台管理员",
            items=[resource_item, backup_item],
            route=route,
            primary_action=action,
            next_step="确认演示资源可用，并在正式试运行前完成一次 SQLite 备份演练。",
        )

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
    async def _ai_contract_item(db: AsyncSession, counts: dict) -> dict:
        agents_result = await db.execute(
            select(AIAgent).where(
                AIAgent.scenario == "lesson_plan",
                AIAgent.enabled.is_(True),
                AIAgent.deleted_at.is_(None),
            )
        )
        agents = agents_result.scalars().all()
        real_agents = [agent for agent in agents if DashboardService._is_real_provider(agent.provider)]

        if not agents:
            return DashboardService._item(
                key="ai_contract",
                label="AI 智能体契约",
                status="error",
                description="教学方案生成需要启用 lesson_plan 智能体配置。",
                metric=f"可用教学方案智能体 {counts['lesson_plan_agents']}",
                action="检查 AI 智能体配置",
                route="/admin/ai-agents",
            )

        misconfigured = [
            agent for agent in real_agents
            if DashboardService._missing_provider_config(agent)
        ]
        if misconfigured:
            missing_names = "、".join(agent.name for agent in misconfigured[:3])
            return DashboardService._item(
                key="ai_contract",
                label="AI 智能体契约",
                status="error",
                description="真实 Provider 智能体还缺少必要配置，补齐前不建议试运行。",
                metric=f"待补齐配置 {len(misconfigured)} / 可用教学方案智能体 {len(agents)}",
                action=f"检查 {missing_names or 'AI 智能体'} 配置",
                route="/admin/ai-agents",
            )

        failure_count = await DashboardService._real_provider_failure_count(db)
        if failure_count:
            return DashboardService._item(
                key="ai_contract",
                label="AI 智能体契约",
                status="warning",
                description="真实 Provider 已出现调用失败，请联动调用记录排查。",
                metric=f"真实 Provider 失败调用 {failure_count}",
                action="查看 AI 调用诊断",
                route="/admin/ai-calls",
            )

        return DashboardService._item(
            key="ai_contract",
            label="AI 智能体契约",
            status="ok",
            description="教学方案生成智能体配置完整。",
            metric=f"可用教学方案智能体 {len(agents)} / 真实 Provider {len(real_agents)}",
            action="检查 AI 智能体配置",
            route="/admin/ai-agents",
        )

    @staticmethod
    def _is_real_provider(provider: Optional[str]) -> bool:
        return (provider or "mock") not in {"mock", "manual_import", "gjt_link"}

    @staticmethod
    def _missing_provider_config(agent: AIAgent) -> list[str]:
        provider = agent.provider or "mock"
        config = agent.config or {}
        missing: list[str] = []
        if not DashboardService._is_real_provider(provider):
            return missing
        if provider == "gjt_api":
            extra = config.get("extra") or {}
            if not (config.get("endpoint") or settings.GJT_API_BASE_URL):
                missing.append("endpoint")
            if not (config.get("agent_id") or extra.get("agent_id") or settings.GJT_AGENT_ID):
                missing.append("agent_id")
            return missing
        api_key_env = config.get("api_key_env")
        has_env_key = bool(api_key_env and os.getenv(api_key_env, ""))
        has_api_key = bool(config.get("api_key") or settings.OPENAI_COMPATIBLE_API_KEY)
        if not (config.get("endpoint") or settings.OPENAI_COMPATIBLE_API_BASE_URL):
            missing.append("endpoint")
        if not (config.get("model") or settings.OPENAI_COMPATIBLE_MODEL):
            missing.append("model")
        if not (has_env_key or has_api_key):
            missing.append("api_key")
        return missing

    @staticmethod
    async def _real_provider_failure_count(db: AsyncSession) -> int:
        query = select(func.count()).select_from(AIAgentCall).where(
            AIAgentCall.status == "failed",
            AIAgentCall.provider.notin_(["mock", "manual_import", "gjt_link"]),
        )
        return int((await db.execute(query)).scalar() or 0)

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
