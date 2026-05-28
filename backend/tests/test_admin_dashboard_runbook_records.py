from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "frontend" / "src" / "views" / "admin" / "AdminDashboard.vue"
API = ROOT / "frontend" / "src" / "api" / "dashboard.ts"
ROUTE_SMOKE = ROOT / "scripts" / "check_frontend_route_smoke.py"


def test_dashboard_api_exposes_trial_runbook_record_contract():
    text = API.read_text(encoding="utf-8")

    for label in [
        "TrialRunbookRecord",
        "TrialRunbookRecordCreate",
        "TrialRunbookRecordStatus",
        "createTrialRunbookRecord",
        "getTrialRunbookRecords",
        "/dashboard/trial-operations/records",
        "/dashboard/trial-operations/stages/${stageKey}/records",
    ]:
        assert label in text


def test_admin_dashboard_renders_runbook_record_workflow():
    text = PAGE.read_text(encoding="utf-8")

    for label in [
        "最近演练记录",
        "记录演练",
        "演练结论",
        "保存记录",
        "createTrialRunbookRecord",
        "getTrialRunbookRecords",
        "recordDialogVisible",
        "recentRunbookRecords",
    ]:
        assert label in text


def test_runbook_record_status_radio_uses_value_prop_to_avoid_console_warning():
    text = PAGE.read_text(encoding="utf-8")

    for status in ["checked", "blocked", "skipped"]:
        assert f'<el-radio-button value="{status}">' in text
        assert f'<el-radio-button label="{status}">' not in text


def test_route_smoke_protects_runbook_record_anchors():
    text = ROUTE_SMOKE.read_text(encoding="utf-8")

    for label in ["最近演练记录", "记录演练"]:
        assert label in text
