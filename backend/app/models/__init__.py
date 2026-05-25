"""SQLAlchemy models for 智跨学评."""

from app.models.user import User
from app.models.role import Role
from app.models.region import Region
from app.models.school import School
from app.models.class_ import Class
from app.models.subject import Subject
from app.models.project import Project
from app.models.project_subject import ProjectSubject
from app.models.project_class import ProjectClass
from app.models.project_lesson import ProjectLesson
from app.models.task import Task
from app.models.submission import Submission
from app.models.rubric import Rubric
from app.models.rubric_item import RubricItem
from app.models.evaluation import Evaluation
from app.models.resource import Resource
from app.models.ai_agent import AIAgent
from app.models.ai_agent_call import AIAgentCall
from app.models.ai_call_step import AICallStep
from app.models.audit_log import AuditLog
from app.models.system_setting import SystemSetting

__all__ = [
    "User",
    "Role",
    "Region",
    "School",
    "Class",
    "Subject",
    "Project",
    "ProjectSubject",
    "ProjectClass",
    "ProjectLesson",
    "Task",
    "Submission",
    "Rubric",
    "RubricItem",
    "Evaluation",
    "Resource",
    "AIAgent",
    "AIAgentCall",
    "AICallStep",
    "AuditLog",
    "SystemSetting",
]
