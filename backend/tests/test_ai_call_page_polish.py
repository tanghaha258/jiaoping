from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "frontend" / "src" / "views" / "admin" / "AICallHistory.vue"


def test_ai_call_page_explains_observability_loop():
    text = PAGE.read_text(encoding="utf-8")

    for label in [
        "AI调用观测",
        "调用链路",
        "思考进度",
        "Provider链路",
        "采纳状态",
        "错误排查",
        "教师采纳门槛",
    ]:
        assert label in text

