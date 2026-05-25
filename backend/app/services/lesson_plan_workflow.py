"""AI lesson-plan workflow service.

This module owns the first deployable AI workflow:
teacher input -> AI draft -> teacher adoption -> real project objects.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.ai_schemas import LESSON_PLAN_THINKING_STEPS, LessonPlanDraftRequest
from app.core.exceptions import (
    AIProviderUnavailableException,
    InvalidStateTransitionException,
    PermissionDeniedException,
    ResourceNotFoundException,
)
from app.db.base import utcnow
from app.models.ai_agent import AIAgent
from app.models.ai_agent_call import AIAgentCall
from app.models.ai_call_step import AICallStep
from app.models.class_ import Class
from app.models.project import Project
from app.models.project_class import ProjectClass
from app.models.project_subject import ProjectSubject
from app.models.resource import Resource
from app.models.rubric import Rubric
from app.models.rubric_item import RubricItem
from app.models.subject import Subject
from app.models.task import Task
from app.models.user import User
from app.services.ai_gateway import AIGateway
from app.services.providers.base import AIProviderRequest

logger = logging.getLogger(__name__)


class LessonPlanWorkflowService:
    """Creates and adopts structured AI teaching-plan drafts."""

    def __init__(self, gateway: AIGateway):
        self.gateway = gateway

    async def get_options(self, db: AsyncSession, user: User) -> dict[str, Any]:
        """Return options needed by the advanced lesson-plan form."""
        subjects_result = await db.execute(select(Subject).order_by(Subject.name))
        classes_result = await db.execute(
            select(Class)
            .where(Class.school_id == user.school_id)
            .order_by(Class.grade, Class.name)
        )
        agents_result = await db.execute(
            select(AIAgent)
            .where(
                AIAgent.scenario == "lesson_plan",
                AIAgent.enabled.is_(True),
                AIAgent.deleted_at.is_(None),
            )
            .order_by(AIAgent.created_at.desc())
        )

        subjects = subjects_result.scalars().all()
        classes = classes_result.scalars().all()
        agents = agents_result.scalars().all()

        return {
            "subjects": [{"id": item.id, "name": item.name} for item in subjects],
            "classes": [
                {"id": item.id, "name": item.name, "grade": item.grade}
                for item in classes
            ],
            "agents": [
                {
                    "id": item.id,
                    "name": item.name,
                    "provider": item.provider,
                    "scenario": item.scenario,
                    "enabled": item.enabled,
                }
                for item in agents
            ],
        }

    async def create_draft(
        self,
        db: AsyncSession,
        body: LessonPlanDraftRequest,
        user: User,
    ) -> dict[str, Any]:
        """Call the configured AI agent and persist a normalized draft."""
        agent = await self._resolve_agent(db, body.agent_id)
        await self._validate_subjects_and_classes(db, body.subject_ids, body.class_ids, user)

        subject_names = await self._subject_names(db, body.subject_ids)
        class_names = await self._class_names(db, body.class_ids)
        input_data = body.model_dump()
        input_data["subjects"] = subject_names
        input_data["classes"] = class_names
        input_data["topic"] = body.theme

        call = AIAgentCall(
            agent_id=agent.id,
            user_id=user.id,
            school_id=user.school_id,
            scenario="lesson_plan",
            provider=agent.provider or "mock",
            input_summary=body.theme,
            request_payload=input_data,
            status="running",
            review_status="pending",
        )
        db.add(call)
        await db.flush()
        await self._complete_step(db, call, "understanding")
        await self._complete_step(db, call, "retrieving_context")

        provider_request = AIProviderRequest(
            scenario="lesson_plan",
            input_data=input_data,
            user_id=user.id,
            school_id=user.school_id,
            project_id=None,
            agent_config=agent.config or {},
        )

        try:
            await self._complete_step(db, call, "drafting")
            result = await self.gateway.execute(
                provider_request,
                {"id": agent.id, "name": agent.name, "provider": agent.provider, "config": agent.config or {}},
            )
        except Exception as exc:
            logger.exception("Lesson-plan provider call failed")
            call.status = "failed"
            call.error_message = str(exc)
            await db.flush()
            raise AIProviderUnavailableException(str(exc))

        if not result.success:
            call.status = "failed"
            call.error_message = result.error_message or "AI provider failed"
            await db.flush()
            raise AIProviderUnavailableException(call.error_message)

        draft = self.normalize_draft(result.content, input_data)
        await self._complete_step(db, call, "normalizing")
        call.status = "succeeded"
        call.response_payload = draft
        call.output_summary = draft["project"]["name"]
        await self._complete_step(db, call, "awaiting_review")
        await db.flush()
        await db.refresh(call)

        return {
            "call_id": call.id,
            "status": call.status,
            "provider": call.provider,
            "draft": draft,
        }

    async def adopt_draft(
        self,
        db: AsyncSession,
        call_id: UUID,
        draft: dict[str, Any] | None,
        user: User,
    ) -> dict[str, Any]:
        """Adopt a reviewed draft into Project, Rubric, Task and Resource rows."""
        result = await db.execute(
            select(AIAgentCall).where(AIAgentCall.id == str(call_id))
        )
        call = result.scalar_one_or_none()
        if call is None:
            raise ResourceNotFoundException(f"AI call not found: {call_id}")
        if call.school_id != user.school_id:
            raise PermissionDeniedException("Cannot adopt another school's AI call")
        if call.status == "adopted" and call.project_id:
            raise InvalidStateTransitionException("This AI draft has already been adopted")
        if call.scenario != "lesson_plan":
            raise InvalidStateTransitionException("Only lesson_plan calls can use this workflow")

        reviewed_draft = self.normalize_draft(draft or call.response_payload or {}, call.request_payload or {})
        project_payload = reviewed_draft["project"]
        await self._validate_subjects_and_classes(
            db,
            project_payload["subject_ids"],
            project_payload["class_ids"],
            user,
        )

        project = Project(
            school_id=user.school_id,
            name=project_payload["name"],
            grade=project_payload["grade"],
            driving_question=project_payload["driving_question"],
            objectives=project_payload.get("objectives", []),
            lesson_count=project_payload["lesson_count"],
            status="active",
            owner_id=user.id,
        )
        db.add(project)
        await db.flush()

        for subject_id in project_payload["subject_ids"]:
            db.add(ProjectSubject(project_id=project.id, subject_id=subject_id))
        for class_id in project_payload["class_ids"]:
            db.add(ProjectClass(project_id=project.id, class_id=class_id))

        rubric_payload = reviewed_draft["rubric"]
        rubric = Rubric(
            school_id=user.school_id,
            name=rubric_payload["name"],
            description=rubric_payload.get("description", ""),
            scope=rubric_payload.get("scope", "personal"),
            created_by=user.id,
        )
        db.add(rubric)
        await db.flush()

        for index, item in enumerate(rubric_payload.get("items", [])):
            db.add(
                RubricItem(
                    rubric_id=rubric.id,
                    dimension=item["dimension"],
                    weight=Decimal(str(item.get("weight", 0))),
                    levels=[
                        {"grade": "A", "description": item.get("level_a", "")},
                        {"grade": "B", "description": item.get("level_b", "")},
                        {"grade": "C", "description": item.get("level_c", "")},
                        {"grade": "D", "description": item.get("level_d", "")},
                    ],
                    sort_order=index,
                )
            )

        tasks: list[Task] = []
        for task_payload in reviewed_draft.get("tasks", []):
            task = Task(
                project_id=project.id,
                title=task_payload["title"],
                description=task_payload.get("description", ""),
                task_type=task_payload.get("task_type", "group"),
                submit_type=task_payload.get("submit_type", "text"),
                rubric_id=rubric.id,
                due_at=None,
                status="draft",
            )
            db.add(task)
            tasks.append(task)

        resources: list[Resource] = []
        for resource_payload in reviewed_draft.get("resources", []):
            resource = Resource(
                school_id=user.school_id,
                title=resource_payload["title"],
                resource_type=resource_payload.get("resource_type", "ai_suggested"),
                url=resource_payload.get("url") or None,
                file_path=None,
                metadata_={
                    "source": "ai_lesson_plan",
                    "call_id": str(call_id),
                    "description": resource_payload.get("description", ""),
                    "suggested_use": resource_payload.get("suggested_use", ""),
                },
                visibility=resource_payload.get("visibility", "school"),
                status="active",
            )
            db.add(resource)
            resources.append(resource)

        call.status = "adopted"
        call.review_status = "approved"
        call.response_payload = reviewed_draft
        call.project_id = project.id
        await db.flush()
        await db.refresh(project)

        loaded_project = await db.execute(
            select(Project)
            .options(
                selectinload(Project.subjects).selectinload(ProjectSubject.subject),
                selectinload(Project.classes).selectinload(ProjectClass.target_class),
            )
            .where(Project.id == project.id)
        )
        project = loaded_project.unique().scalar_one()

        return {
            "call_id": call.id,
            "project": self._project_dict(project),
            "rubric": {"id": rubric.id, "name": rubric.name},
            "tasks": [{"id": item.id, "title": item.title, "status": item.status} for item in tasks],
            "resources": [{"id": item.id, "title": item.title} for item in resources],
        }

    def normalize_draft(self, content: Any, source_input: dict[str, Any]) -> dict[str, Any]:
        """Normalize provider output to the workflow's fixed draft structure."""
        if not isinstance(content, dict):
            raise InvalidStateTransitionException("AI draft must be a JSON object")

        if all(key in content for key in ("project", "tasks", "rubric", "resources", "teacher_notes")):
            return self._complete_standard_draft(content, source_input)

        lessons = content.get("lessons") or []
        theme = content.get("theme") or source_input.get("theme") or source_input.get("topic") or "跨学科主题学习"
        lesson_count = int(source_input.get("lesson_count") or len(lessons) or 1)
        objectives = source_input.get("core_competencies") or []
        if not objectives:
            objectives = [
                lesson.get("objectives")
                for lesson in lessons[:3]
                if isinstance(lesson, dict) and lesson.get("objectives")
            ]

        tasks = []
        for index in range(lesson_count):
            lesson = lessons[index] if index < len(lessons) and isinstance(lessons[index], dict) else {}
            title = lesson.get("title") or f"第{index + 1}课时：{theme}"
            description_parts = [
                f"学习目标：{lesson.get('objectives', '')}",
                f"课堂活动：{lesson.get('activities', '')}",
                f"学习材料：{lesson.get('materials', '')}",
                f"建议时长：{lesson.get('duration', '45分钟')}",
            ]
            tasks.append(
                {
                    "title": title,
                    "description": "\n".join(part for part in description_parts if not part.endswith("：")),
                    "task_type": "group" if index in (1, 2, 3) else "individual",
                    "submit_type": "mixed" if index == lesson_count - 1 else "text",
                }
            )

        return self._complete_standard_draft(
            {
                "project": {
                    "name": theme,
                    "grade": source_input.get("grade", "七年级"),
                    "subject_ids": source_input.get("subject_ids", []),
                    "class_ids": source_input.get("class_ids", []),
                    "driving_question": content.get("driving_question") or f"我们如何综合运用多学科知识解决“{theme}”这一真实问题？",
                    "lesson_count": lesson_count,
                    "objectives": objectives,
                },
                "tasks": tasks,
                "rubric": self._default_rubric(theme, content.get("assessment_plan")),
                "resources": self._default_resources(theme, source_input),
                "teacher_notes": [
                    "AI 已生成项目、课时任务、评价量规与资源建议。",
                    "采纳后项目会立即激活，任务保持草稿，需教师确认后再发布给学生。",
                ],
            },
            source_input,
        )

    def _complete_standard_draft(self, draft: dict[str, Any], source_input: dict[str, Any]) -> dict[str, Any]:
        project = draft.get("project") or {}
        tasks = draft.get("tasks") or []
        rubric = draft.get("rubric") or {}
        resources = draft.get("resources") or []

        project_name = (project.get("name") or source_input.get("theme") or source_input.get("topic") or "跨学科主题学习").strip()
        lesson_count = int(project.get("lesson_count") or source_input.get("lesson_count") or max(len(tasks), 1))
        normalized = {
            "project": {
                "name": project_name,
                "grade": project.get("grade") or source_input.get("grade") or "七年级",
                "subject_ids": project.get("subject_ids") or source_input.get("subject_ids") or [],
                "class_ids": project.get("class_ids") or source_input.get("class_ids") or [],
                "driving_question": project.get("driving_question") or f"我们如何综合运用多学科知识解决“{project_name}”这一真实问题？",
                "lesson_count": lesson_count,
                "objectives": project.get("objectives") or source_input.get("core_competencies") or [],
            },
            "tasks": [self._normalize_task(item, index, project_name) for index, item in enumerate(tasks[:lesson_count])],
            "rubric": self._normalize_rubric(rubric, project_name),
            "resources": [self._normalize_resource(item, project_name) for item in resources[:8]],
            "teacher_notes": draft.get("teacher_notes") or [],
        }
        if not normalized["tasks"]:
            normalized["tasks"] = [
                self._normalize_task({"title": f"第{i + 1}课时：{project_name}"}, i, project_name)
                for i in range(lesson_count)
            ]
        if not normalized["resources"]:
            normalized["resources"] = self._default_resources(project_name, source_input)
        return normalized

    def _normalize_task(self, item: dict[str, Any], index: int, project_name: str) -> dict[str, str]:
        allowed_task_types = {"individual", "group", "classroom", "homework"}
        allowed_submit_types = {"text", "file", "link", "mixed"}
        task_type = item.get("task_type") or ("group" if index > 0 else "individual")
        submit_type = item.get("submit_type") or "text"
        return {
            "title": item.get("title") or f"第{index + 1}课时：{project_name}",
            "description": item.get("description") or item.get("activities") or "围绕主题完成学习任务并提交过程记录。",
            "task_type": task_type if task_type in allowed_task_types else "group",
            "submit_type": submit_type if submit_type in allowed_submit_types else "text",
        }

    def _normalize_rubric(self, rubric: dict[str, Any], project_name: str) -> dict[str, Any]:
        normalized = {
            "name": rubric.get("name") or f"{project_name}学习评价量规",
            "description": rubric.get("description") or "用于评价学生在跨学科主题学习中的综合表现。",
            "scope": rubric.get("scope") or "personal",
            "items": rubric.get("items") or self._default_rubric(project_name).get("items", []),
        }
        total_weight = sum(float(item.get("weight", 0)) for item in normalized["items"])
        if not total_weight:
            normalized["items"] = self._default_rubric(project_name)["items"]
        return normalized

    def _normalize_resource(self, item: dict[str, Any], project_name: str) -> dict[str, Any]:
        resource_type = item.get("resource_type") or item.get("type") or "ai_suggested"
        return {
            "title": item.get("title") or f"{project_name}学习资源",
            "resource_type": resource_type,
            "description": item.get("description") or "",
            "suggested_use": item.get("suggested_use") or "",
            "url": item.get("url") or "",
            "visibility": item.get("visibility") or "school",
        }

    def _default_rubric(self, theme: str, description: str | None = None) -> dict[str, Any]:
        return {
            "name": f"{theme}跨学科探究评价量规",
            "description": description or "聚焦知识理解、探究过程、跨学科迁移、合作表达和成果质量。",
            "scope": "personal",
            "items": [
                self._rubric_item("知识理解", 20),
                self._rubric_item("探究过程", 25),
                self._rubric_item("跨学科迁移", 20),
                self._rubric_item("合作表达", 15),
                self._rubric_item("成果质量", 20),
            ],
        }

    def _rubric_item(self, dimension: str, weight: int) -> dict[str, Any]:
        return {
            "dimension": dimension,
            "weight": weight,
            "level_a": "表现突出，证据充分，能够独立迁移应用。",
            "level_b": "达到要求，能够完成主要任务并说明理由。",
            "level_c": "基本完成，需要教师或同伴提供一定支持。",
            "level_d": "完成度不足，需要重新梳理任务要求并获得持续支持。",
        }

    def _default_resources(self, theme: str, source_input: dict[str, Any]) -> list[dict[str, Any]]:
        grade = source_input.get("grade", "七年级")
        return [
            {
                "title": f"{theme}项目学习任务单",
                "resource_type": "task_sheet",
                "description": f"面向{grade}学生的项目学习过程记录单。",
                "suggested_use": "用于课前导入、过程记录和小组协作分工。",
                "visibility": "school",
            },
            {
                "title": f"{theme}资料阅读包",
                "resource_type": "document",
                "description": "包含多学科背景资料、问题链和阅读提示。",
                "suggested_use": "用于课堂探究和分层阅读支持。",
                "visibility": "school",
            },
            {
                "title": f"{theme}成果展示模板",
                "resource_type": "template",
                "description": "用于汇报、海报或倡议书展示的结构化模板。",
                "suggested_use": "用于最终成果整理与同伴互评。",
                "visibility": "school",
            },
        ]

    async def _complete_step(
        self,
        db: AsyncSession,
        call: AIAgentCall,
        step_code: str,
    ) -> None:
        """Create or mark one workflow thinking step as completed."""
        step_defs = {item["code"]: item for item in LESSON_PLAN_THINKING_STEPS}
        step_def = step_defs[step_code]
        step_order = [item["code"] for item in LESSON_PLAN_THINKING_STEPS].index(step_code)
        now = utcnow()

        result = await db.execute(
            select(AICallStep).where(
                AICallStep.call_id == call.id,
                AICallStep.code == step_code,
                AICallStep.deleted_at.is_(None),
            )
        )
        step = result.scalar_one_or_none()
        if step is None:
            step = AICallStep(
                call_id=call.id,
                code=step_code,
                title=step_def["title"],
                description=step_def.get("description", ""),
                status="completed",
                percent=step_def["percent"],
                sort_order=step_order,
                started_at=now,
                completed_at=now,
            )
            db.add(step)
        else:
            step.title = step_def["title"]
            step.description = step_def.get("description", "")
            step.status = "completed"
            step.percent = step_def["percent"]
            step.sort_order = step_order
            step.started_at = step.started_at or now
            step.completed_at = now
        await db.flush()

    async def _resolve_agent(self, db: AsyncSession, agent_id: str | None) -> AIAgent:
        query = select(AIAgent).where(
            AIAgent.scenario == "lesson_plan",
            AIAgent.enabled.is_(True),
            AIAgent.deleted_at.is_(None),
        )
        if agent_id:
            query = query.where(AIAgent.id == str(agent_id))
        query = query.order_by(AIAgent.created_at.desc())
        result = await db.execute(query)
        agent = result.scalars().first()
        if agent is None:
            raise ResourceNotFoundException("No enabled lesson_plan AI agent was found")
        return agent

    async def _validate_subjects_and_classes(
        self,
        db: AsyncSession,
        subject_ids: list[str],
        class_ids: list[str],
        user: User,
    ) -> None:
        subjects_result = await db.execute(select(Subject.id).where(Subject.id.in_(subject_ids)))
        found_subjects = set(subjects_result.scalars().all())
        missing_subjects = set(subject_ids) - found_subjects
        if missing_subjects:
            raise ResourceNotFoundException(f"Subjects not found: {', '.join(sorted(missing_subjects))}")

        classes_result = await db.execute(
            select(Class.id).where(Class.id.in_(class_ids), Class.school_id == user.school_id)
        )
        found_classes = set(classes_result.scalars().all())
        missing_classes = set(class_ids) - found_classes
        if missing_classes:
            raise ResourceNotFoundException(f"Classes not found in current school: {', '.join(sorted(missing_classes))}")

    async def _subject_names(self, db: AsyncSession, subject_ids: list[str]) -> list[str]:
        result = await db.execute(select(Subject).where(Subject.id.in_(subject_ids)))
        by_id = {item.id: item.name for item in result.scalars().all()}
        return [by_id.get(item_id, item_id) for item_id in subject_ids]

    async def _class_names(self, db: AsyncSession, class_ids: list[str]) -> list[str]:
        result = await db.execute(select(Class).where(Class.id.in_(class_ids)))
        by_id = {item.id: item.name for item in result.scalars().all()}
        return [by_id.get(item_id, item_id) for item_id in class_ids]

    def _project_dict(self, project: Project) -> dict[str, Any]:
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
            "subjects": [
                {"id": item.subject.id, "name": item.subject.name}
                for item in project.subjects
                if item.subject
            ],
            "classes": [
                {"id": item.target_class.id, "name": item.target_class.name, "grade": item.target_class.grade}
                for item in project.classes
                if item.target_class
            ],
        }
