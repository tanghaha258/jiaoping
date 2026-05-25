"""Database seeding: idempotently create baseline data for first deployment."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.ai_agent import AIAgent
from app.models.class_ import Class
from app.models.evaluation import Evaluation
from app.models.project import Project
from app.models.project_class import ProjectClass
from app.models.project_subject import ProjectSubject
from app.models.region import Region
from app.models.resource import Resource
from app.models.rubric import Rubric
from app.models.rubric_item import RubricItem
from app.models.school import School
from app.models.subject import Subject
from app.models.submission import Submission
from app.models.task import Task
from app.models.user import User

ModelT = TypeVar("ModelT")

REGION_ID = "region-00000000-0000-0000-0001"
SCHOOL_ID = "school-00000000-0000-0000-0001"
CLASS_ID = "class-00000000-0000-0000-0001"
ADMIN_ID = "user-admin-000000-0000-0000-0001"
TEACHER_ID = "user-teacher-0000-0000-0000-0001"
TEACHER_2_ID = "user-teacher-0000-0000-0000-0002"
PROJECT_ID = "project-ocean-0000-0000-0000000001"
RUBRIC_ID = "rubric-interdisciplinary-0001"
TASK_1_ID = "task-ocean-0000-0000-000000000001"
TASK_2_ID = "task-ocean-0000-0000-000000000002"
SUBMISSION_1_ID = "submission-ocean-0000-000000000001"
EVALUATION_1_ID = "evaluation-ocean-0000-000000000001"


async def _get(db: AsyncSession, model: type[ModelT], item_id: str) -> ModelT | None:
    return await db.get(model, item_id)


async def _add_if_missing(
    db: AsyncSession,
    model: type[ModelT],
    item_id: str,
    **kwargs,
) -> ModelT:
    item = await _get(db, model, item_id)
    if item is None:
        item = model(id=item_id, **kwargs)
        db.add(item)
    return item


async def seed_database(db: AsyncSession) -> None:
    """Seed a usable MVP dataset without duplicating rows on restart."""

    await _seed_organization(db)
    await _seed_users(db)
    await _seed_subjects(db)
    await _seed_ai_agents(db)
    await _seed_operational_demo(db)
    print("Seed data ensured successfully")


async def _seed_organization(db: AsyncSession) -> None:
    await _add_if_missing(
        db,
        Region,
        REGION_ID,
        name="钦州市",
        code="qz",
    )
    await _add_if_missing(
        db,
        School,
        SCHOOL_ID,
        region_id=REGION_ID,
        name="钦州市第一中学",
        code="qz01",
        status="active",
    )
    await _add_if_missing(
        db,
        Class,
        CLASS_ID,
        school_id=SCHOOL_ID,
        grade="七年级",
        name="七年级(1)班",
        academic_year="2025-2026",
    )


async def _seed_users(db: AsyncSession) -> None:
    users = [
        (ADMIN_ID, "admin", "admin123", "系统管理员", "system_admin", None),
        (TEACHER_ID, "teacher001", "password", "张老师", "teacher", None),
        (TEACHER_2_ID, "teacher002", "password", "李老师", "teacher", None),
        ("user-school-admin-0000-0000001", "schooladmin", "password", "学校管理员", "school_admin", None),
        ("user-researcher-0000-0000001", "researcher001", "password", "教研员王老师", "researcher", None),
        ("user-student-0000-0000-0000-0001", "student001", "password", "学生一", "student", CLASS_ID),
        ("user-student-0000-0000-0000-0002", "student002", "password", "学生二", "student", CLASS_ID),
        ("user-student-0000-0000-0000-0003", "student003", "password", "学生三", "student", CLASS_ID),
        ("user-student-0000-0000-0000-0004", "student004", "password", "学生四", "student", CLASS_ID),
        ("user-student-0000-0000-0000-0005", "student005", "password", "学生五", "student", CLASS_ID),
    ]

    for user_id, username, password, name, role, class_id in users:
        existing = await db.execute(select(User).where(User.username == username))
        if existing.scalar_one_or_none() is None:
            db.add(
                User(
                    id=user_id,
                    username=username,
                    password_hash=hash_password(password),
                    name=name,
                    role=role,
                    school_id=SCHOOL_ID,
                    class_id=class_id,
                    status="active",
                )
            )


async def _seed_subjects(db: AsyncSession) -> None:
    subject_list = [
        ("subject-00000000-0000-0000-0001", "语文"),
        ("subject-00000000-0000-0000-0002", "数学"),
        ("subject-00000000-0000-0000-0003", "英语"),
        ("subject-00000000-0000-0000-0004", "地理"),
        ("subject-00000000-0000-0000-0005", "生物"),
        ("subject-00000000-0000-0000-0006", "道法"),
        ("subject-00000000-0000-0000-0007", "信息科技"),
    ]

    for subject_id, name in subject_list:
        await _add_if_missing(
            db,
            Subject,
            subject_id,
            name=name,
            stage="junior_high",
        )


async def _seed_ai_agents(db: AsyncSession) -> None:
    agents = [
        (
            "agent-lesson-plan-0000-0000-0001",
            "教案生成智能体",
            "lesson_plan",
            {"type": "object", "properties": {"grade": "string", "subjects": "string", "topic": "string"}},
            {"type": "object", "properties": {"lesson_plan": "string"}},
        ),
        (
            "agent-learning-diag-0000-0001",
            "学习诊断智能体",
            "learning_diagnosis",
            {"type": "object", "properties": {"submission_content": "string", "rubric": "object"}},
            {"type": "object", "properties": {"diagnosis": "object", "scores": "object"}},
        ),
        (
            "agent-rubric-gen-0000-0000001",
            "量规生成智能体",
            "rubric_generation",
            {"type": "object", "properties": {"task_description": "string", "grade": "string"}},
            {"type": "object", "properties": {"rubric": "object"}},
        ),
        (
            "agent-teach-refl-0000-0000001",
            "教学反思智能体",
            "teaching_reflection",
            {"type": "object", "properties": {"lesson_plan": "object", "student_results": "object"}},
            {"type": "object", "properties": {"reflection": "object"}},
        ),
    ]

    for agent_id, name, scenario, input_schema, output_schema in agents:
        await _add_if_missing(
            db,
            AIAgent,
            agent_id,
            name=name,
            provider="mock",
            scenario=scenario,
            config={"model": "mock", "temperature": 0.6},
            input_schema=input_schema,
            output_schema=output_schema,
            enabled=True,
        )


async def _seed_operational_demo(db: AsyncSession) -> None:
    now = datetime.now(timezone.utc)

    await _add_if_missing(
        db,
        Project,
        PROJECT_ID,
        school_id=SCHOOL_ID,
        name="保护海洋，从我做起",
        grade="七年级",
        driving_question="如何减少生活中的海洋污染，并用跨学科证据提出可执行的校园倡议？",
        objectives=[
            "理解海洋生态系统的基本结构和污染影响。",
            "能够收集、整理并可视化海洋污染案例数据。",
            "完成一份有证据支撑的校园环保倡议书。",
        ],
        lesson_count=5,
        status="active",
        owner_id=TEACHER_ID,
    )

    for subject_id in [
        "subject-00000000-0000-0000-0001",
        "subject-00000000-0000-0000-0004",
        "subject-00000000-0000-0000-0005",
        "subject-00000000-0000-0000-0007",
    ]:
        if await db.get(ProjectSubject, {"project_id": PROJECT_ID, "subject_id": subject_id}) is None:
            db.add(ProjectSubject(project_id=PROJECT_ID, subject_id=subject_id))

    if await db.get(ProjectClass, {"project_id": PROJECT_ID, "class_id": CLASS_ID}) is None:
        db.add(ProjectClass(project_id=PROJECT_ID, class_id=CLASS_ID))

    await _seed_rubric(db)

    await _add_if_missing(
        db,
        Task,
        TASK_1_ID,
        project_id=PROJECT_ID,
        title="课时一：认识海洋生态系统",
        description="通过图文资料和视频案例梳理海洋生态系统的组成与相互关系。",
        task_type="reading",
        submit_type="text",
        rubric_id=RUBRIC_ID,
        due_at=now + timedelta(days=2),
        status="published",
    )
    await _add_if_missing(
        db,
        Task,
        TASK_2_ID,
        project_id=PROJECT_ID,
        title="课时二：海洋污染案例调查",
        description="小组选择一个海洋污染案例，完成成因、影响和治理措施分析。",
        task_type="discussion",
        submit_type="text",
        rubric_id=RUBRIC_ID,
        due_at=now + timedelta(days=3),
        status="published",
    )

    await _add_if_missing(
        db,
        Submission,
        SUBMISSION_1_ID,
        task_id=TASK_2_ID,
        student_id="user-student-0000-0000-0000-0001",
        group_name="海洋观察小组",
        content="我们调查了近岸塑料垃圾对海鸟和鱼类的影响，整理了污染来源、影响链条和校园减塑建议。",
        attachments=[],
        status="submitted",
        submitted_at=now - timedelta(hours=4),
    )

    await _add_if_missing(
        db,
        Evaluation,
        EVALUATION_1_ID,
        submission_id=SUBMISSION_1_ID,
        evaluator_id=TEACHER_ID,
        evaluator_type="teacher",
        rubric_id=RUBRIC_ID,
        scores={"知识理解": 18, "探究能力": 17, "跨学科迁移": 18, "合作表达": 16, "行动方案": 17},
        comments="整体完成度较高，能用真实案例支撑观点。建议补充数据来源说明。",
        status="draft",
        confirmed_by=None,
    )

    await _seed_resources(db)


async def _seed_rubric(db: AsyncSession) -> None:
    await _add_if_missing(
        db,
        Rubric,
        RUBRIC_ID,
        school_id=SCHOOL_ID,
        name="跨学科探究评价量规",
        description="用于评价学生在跨学科主题项目中的知识理解、探究能力、迁移表达和行动方案。",
        scope="school",
        created_by=TEACHER_ID,
    )

    items = [
        ("rubric-item-knowledge-0001", "知识理解", Decimal("20.00"), 1),
        ("rubric-item-inquiry-0001", "探究能力", Decimal("20.00"), 2),
        ("rubric-item-transfer-0001", "跨学科迁移", Decimal("20.00"), 3),
        ("rubric-item-expression-0001", "合作表达", Decimal("20.00"), 4),
        ("rubric-item-action-0001", "行动方案", Decimal("20.00"), 5),
    ]

    levels = [
        {"level": "A", "description": "表现突出，证据充分，能够独立迁移应用。"},
        {"level": "B", "description": "达到要求，能完成主要任务并说明理由。"},
        {"level": "C", "description": "基本完成，需要教师或同伴支持。"},
        {"level": "D", "description": "完成度不足，需要重新梳理任务。"},
    ]

    for item_id, dimension, weight, sort_order in items:
        await _add_if_missing(
            db,
            RubricItem,
            item_id,
            rubric_id=RUBRIC_ID,
            dimension=dimension,
            weight=weight,
            levels=levels,
            sort_order=sort_order,
        )


async def _seed_resources(db: AsyncSession) -> None:
    resources = [
        ("resource-ocean-design-0001", "海洋生态保护教学设计", "teaching_design", ["七年级", "地理", "生物", "跨学科"]),
        ("resource-wetland-task-0001", "湿地与生物多样性PBL任务", "task_sheet", ["七年级", "地理", "语文", "PBL"]),
        ("resource-rubric-0001", "跨学科探究评价量规模板", "rubric", ["评价", "量规", "能力维度"]),
        ("resource-ocean-video-0001", "海洋污染与治理微课", "micro_lesson", ["微课", "海洋保护"]),
    ]

    for resource_id, title, resource_type, tags in resources:
        await _add_if_missing(
            db,
            Resource,
            resource_id,
            school_id=SCHOOL_ID,
            title=title,
            resource_type=resource_type,
            file_path=None,
            url=None,
            metadata_={"grade": "七年级", "tags": tags, "source": "seed"},
            visibility="school",
            status="published",
        )
