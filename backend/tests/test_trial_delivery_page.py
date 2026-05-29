from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "frontend" / "src" / "api" / "dashboard.ts"
ROUTES = ROOT / "frontend" / "src" / "router" / "routes.ts"
ROLE_MENU = ROOT / "frontend" / "src" / "layouts" / "RoleMenu.vue"
PAGE = ROOT / "frontend" / "src" / "views" / "admin" / "TrialDeliveryPackage.vue"
ROUTE_SMOKE = ROOT / "scripts" / "check_frontend_route_smoke.py"


def test_dashboard_api_exposes_trial_delivery_package_contract():
    text = API.read_text(encoding="utf-8")

    for label in [
        "TrialDeliveryPackage",
        "TrialDeliveryChecklistItem",
        "TrialDeliveryDemoStep",
        "TrialDeliveryAccount",
        "TrialDeliveryPrintableAcceptance",
        "TrialDeliveryFallbackProcedure",
        "TrialDeliveryRoleHandoff",
        "getTrialDeliveryPackage",
        "/dashboard/trial-delivery/package",
    ]:
        assert label in text


def test_admin_route_and_menu_include_trial_delivery_page():
    routes = ROUTES.read_text(encoding="utf-8")
    role_menu = ROLE_MENU.read_text(encoding="utf-8")

    for label in [
        "path: 'trial-delivery'",
        "TrialDeliveryPackage",
        "试点交付包",
    ]:
        assert label in routes

    for label in [
        "/admin/trial-delivery",
        "试点交付包",
    ]:
        assert label in role_menu


def test_trial_delivery_page_renders_package_workflow():
    assert PAGE.exists(), f"Missing page: {PAGE}"
    text = PAGE.read_text(encoding="utf-8")

    for label in [
        "试点交付包",
        "现场验收清单",
        "演示脚本",
        "测试账号交付",
        "打印验收说明",
        "异常处置流程",
        "分角色交接卡",
        "复制交付材料",
        "下载 Markdown",
        "下载 JSON",
        "getTrialDeliveryPackage",
        "downloadMarkdown",
        "downloadJson",
        "copyMarkdown",
    ]:
        assert label in text


def test_route_smoke_protects_trial_delivery_page():
    text = ROUTE_SMOKE.read_text(encoding="utf-8")

    for label in [
        "path: 'trial-delivery'",
        "TrialDeliveryPackage.vue",
        "试点交付包",
        "现场验收清单",
        "打印验收说明",
        "异常处置流程",
        "分角色交接卡",
        "下载 Markdown",
    ]:
        assert label in text
