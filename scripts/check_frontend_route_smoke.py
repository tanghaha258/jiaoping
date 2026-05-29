from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SRC = ROOT / "frontend" / "src"
ROUTES_FILE = FRONTEND_SRC / "router" / "routes.ts"


@dataclass(frozen=True)
class RouteExpectation:
    path_marker: str
    component: str
    title: str
    anchors: tuple[str, ...] = ()


ROUTE_EXPECTATIONS: tuple[RouteExpectation, ...] = (
    RouteExpectation("path: '/login'", "views/login/LoginPage.vue", "登录", ("智跨学评",)),
    RouteExpectation("path: '/teacher'", "layouts/AppLayout.vue", "教师工作台"),
    RouteExpectation("path: ''", "views/teacher/TeacherDashboard.vue", "工作台", ("跨学科教学评一体化工作台", "快捷入口")),
    RouteExpectation("path: 'ai/lesson-plan'", "views/teacher/AILessonPlan.vue", "AI教学方案", ("AI生成教学方案", "AI草案审阅")),
    RouteExpectation("path: 'projects'", "views/teacher/ProjectList.vue", "项目管理", ("跨学科项目管理", "AI 生成教学方案")),
    RouteExpectation("path: 'projects/:id'", "views/teacher/ProjectDetail.vue", "项目详情", ("项目概览", "课时任务")),
    RouteExpectation("path: 'tasks/:id/submissions'", "views/teacher/SubmissionReview.vue", "提交审核", ("提交审阅", "学生提交")),
    RouteExpectation("path: 'evaluations'", "views/teacher/EvaluationCenter.vue", "评价中心", ("评价中心", "评价记录")),
    RouteExpectation("path: 'resources'", "views/teacher/ResourceCenter.vue", "资源中心", ("资源中心", "新增资源")),
    RouteExpectation("path: 'settings'", "views/teacher/TeacherSettings.vue", "系统设置", ("账号安全", "更新密码")),
    RouteExpectation("path: '/student'", "layouts/AppLayout.vue", "学生学习"),
    RouteExpectation("path: ''", "views/student/StudentDashboard.vue", "学习概览", ("学习概览",)),
    RouteExpectation("path: 'tasks'", "views/student/StudentTaskList.vue", "学习任务", ("我的任务",)),
    RouteExpectation("path: 'tasks/:id'", "views/student/StudentTaskDetail.vue", "任务详情", ("任务详情", "我的提交")),
    RouteExpectation("path: 'profile'", "views/student/StudentProfile.vue", "我的档案", ("我的档案",)),
    RouteExpectation("path: '/research'", "layouts/AppLayout.vue", "教研工作台"),
    RouteExpectation("path: ''", "views/research/ResearchDashboard.vue", "工作台", ("教研工作台",)),
    RouteExpectation("path: 'templates'", "views/research/TemplateList.vue", "模板管理", ("模板管理",)),
    RouteExpectation("path: 'resources'", "views/research/ResourceReview.vue", "资源审核", ("资源审核",)),
    RouteExpectation("path: '/admin'", "layouts/AppLayout.vue", "管理后台"),
    RouteExpectation("path: ''", "views/admin/AdminDashboard.vue", "驾驶舱", ("管理驾驶舱", "试运行检查清单", "试运行演练台", "演练阶段", "Provider演练", "记录演练", "最近演练记录")),
    RouteExpectation("path: 'trial-delivery'", "views/admin/TrialDeliveryPackage.vue", "试点交付包", ("试点交付包", "现场验收清单", "演示脚本", "测试账号交付", "打印验收说明", "异常处置流程", "分角色交接卡", "下载 Markdown", "下载 JSON", "复制交付材料")),
    RouteExpectation("path: 'users'", "views/admin/UserManagement.vue", "用户管理", ("用户管理", "导入账号包")),
    RouteExpectation("path: 'schools'", "views/admin/SchoolManagement.vue", "学校管理", ("学校管理", "导入数据包")),
    RouteExpectation("path: 'ai-agents'", "views/admin/AIAgentConfig.vue", "AI智能体", ("AI智能体治理", "本地契约层", "Provider适配")),
    RouteExpectation("path: 'ai-calls'", "views/admin/AICallHistory.vue", "AI调用", ("AI调用观测", "调用链路", "思考进度", "失败诊断")),
    RouteExpectation("path: 'audit-logs'", "views/admin/AuditLogViewer.vue", "审计日志", ("审计日志", "日志记录")),
    RouteExpectation("path: 'settings'", "views/admin/SystemSettings.vue", "系统设置", ("系统设置",)),
)


def read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise AssertionError(f"{relative(path)} is not valid UTF-8: {exc}") from exc


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def component_import_marker(component: str) -> str:
    return f"@/{component}"


def title_marker(title: str) -> str:
    return f"title: '{title}'"


def compact_template_text(text: str) -> str:
    without_script = re.sub(r"<script[\s\S]*?</script>", "", text)
    without_style = re.sub(r"<style[\s\S]*?</style>", "", without_script)
    return re.sub(r"\s+", " ", without_style)


def check_routes() -> list[str]:
    errors: list[str] = []
    if not ROUTES_FILE.exists():
        return [f"{relative(ROUTES_FILE)} is missing"]

    routes_text = read_utf8(ROUTES_FILE)
    checked_components: set[Path] = set()

    for expectation in ROUTE_EXPECTATIONS:
        route_label = f"{expectation.path_marker} -> {expectation.component}"
        if expectation.path_marker not in routes_text:
            errors.append(f"{route_label}: route path marker missing")

        import_marker = component_import_marker(expectation.component)
        if import_marker not in routes_text:
            errors.append(f"{route_label}: component import marker {import_marker!r} missing")

        if title_marker(expectation.title) not in routes_text:
            errors.append(f"{route_label}: route title {expectation.title!r} missing")

        component_path = FRONTEND_SRC / expectation.component
        if not component_path.exists():
            errors.append(f"{route_label}: component file missing at {relative(component_path)}")
            continue

        if expectation.anchors and component_path not in checked_components:
            component_text = compact_template_text(read_utf8(component_path))
            for anchor in expectation.anchors:
                if anchor not in component_text:
                    errors.append(f"{relative(component_path)}: page anchor {anchor!r} missing")
            checked_components.add(component_path)

    return errors


def main() -> int:
    errors = check_routes()
    if errors:
        print("Frontend route smoke check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Frontend route smoke check passed. checked_routes={len(ROUTE_EXPECTATIONS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
