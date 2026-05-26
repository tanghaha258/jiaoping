import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_frontend_route_smoke_script_exists_and_passes():
    script = ROOT / "scripts" / "check_frontend_route_smoke.py"

    assert script.exists(), f"Missing frontend route smoke script: {script}"

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Frontend route smoke check passed." in result.stdout
    assert "checked_routes=" in result.stdout


def test_release_check_runs_frontend_route_smoke_script():
    release_script = (ROOT / "scripts" / "check-release.ps1").read_text(encoding="utf-8")

    assert "check_frontend_route_smoke.py" in release_script


def test_core_route_files_and_page_anchors_are_declared():
    routes = (ROOT / "frontend" / "src" / "router" / "routes.ts").read_text(encoding="utf-8")

    for route_path, component_file, title in [
        ("path: '/login'", "LoginPage.vue", "登录"),
        ("path: '/teacher'", "AppLayout.vue", "教师工作台"),
        ("path: 'ai/lesson-plan'", "AILessonPlan.vue", "AI教学方案"),
        ("path: 'projects'", "ProjectList.vue", "项目管理"),
        ("path: '/student'", "AppLayout.vue", "学生学习"),
        ("path: 'tasks'", "StudentTaskList.vue", "学习任务"),
        ("path: '/research'", "AppLayout.vue", "教研工作台"),
        ("path: 'templates'", "TemplateList.vue", "模板管理"),
        ("path: '/admin'", "AppLayout.vue", "管理后台"),
        ("path: 'ai-agents'", "AIAgentConfig.vue", "AI智能体"),
        ("path: 'settings'", "SystemSettings.vue", "系统设置"),
    ]:
        assert route_path in routes
        assert component_file in routes
        assert title in routes
