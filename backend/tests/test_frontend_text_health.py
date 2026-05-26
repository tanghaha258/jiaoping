import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_frontend_text_health_script_exists_and_passes():
    script = ROOT / "scripts" / "check_frontend_text_health.py"

    assert script.exists(), f"Missing frontend text health script: {script}"

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Frontend text health check passed." in result.stdout


def test_release_check_runs_frontend_text_health_script():
    release_script = (ROOT / "scripts" / "check-release.ps1").read_text(encoding="utf-8")

    assert "check_frontend_text_health.py" in release_script


def test_core_frontend_labels_are_present_as_utf8_text():
    routes = (ROOT / "frontend" / "src" / "router" / "routes.ts").read_text(encoding="utf-8")
    router = (ROOT / "frontend" / "src" / "router" / "index.ts").read_text(encoding="utf-8")
    app_layout = (ROOT / "frontend" / "src" / "layouts" / "AppLayout.vue").read_text(encoding="utf-8")
    role_menu = (ROOT / "frontend" / "src" / "layouts" / "RoleMenu.vue").read_text(encoding="utf-8")

    for label in [
        "登录",
        "教师工作台",
        "AI教学方案",
        "学生学习",
        "教研工作台",
        "管理后台",
        "AI智能体",
        "404 页面未找到",
    ]:
        assert label in routes

    assert "智跨学评" in router

    for label in ["跨学科教学评一体化", "AI智能体平台", "智能备课", "智能评价"]:
        assert label in app_layout

    for label in [
        "教学核心应用",
        "AI生成教学方案",
        "跨学科任务设计",
        "学情诊断与分析",
        "平台治理",
        "审计日志",
    ]:
        assert label in role_menu
