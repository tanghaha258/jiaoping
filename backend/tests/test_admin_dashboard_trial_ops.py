from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "frontend" / "src" / "views" / "admin" / "AdminDashboard.vue"
API = ROOT / "frontend" / "src" / "api" / "dashboard.ts"
ROUTE_SMOKE = ROOT / "scripts" / "check_frontend_route_smoke.py"


def test_admin_dashboard_renders_trial_operations_runbook_panel():
    text = PAGE.read_text(encoding="utf-8")

    for label in [
        "试运行演练台",
        "演练阶段",
        "责任角色",
        "证据",
        "下一步",
        "Provider演练",
        "getTrialOperationsRunbook",
        "trialRunbook",
    ]:
        assert label in text


def test_dashboard_api_exposes_trial_operations_runbook_contract():
    text = API.read_text(encoding="utf-8")

    for label in [
        "TrialOperationsRunbook",
        "TrialOperationsStage",
        "getTrialOperationsRunbook",
        "/dashboard/trial-operations/runbook",
    ]:
        assert label in text


def test_route_smoke_protects_trial_operations_runbook_anchors():
    text = ROUTE_SMOKE.read_text(encoding="utf-8")

    for label in ["试运行演练台", "演练阶段", "Provider演练"]:
        assert label in text
