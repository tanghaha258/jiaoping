from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "frontend" / "src" / "views" / "admin" / "AIAgentConfig.vue"


def test_ai_agent_page_explains_contract_governance():
    text = PAGE.read_text(encoding="utf-8")

    for label in [
        "AI智能体治理",
        "本地契约层",
        "Provider适配",
        "教师采纳门槛",
        "桂教通预留",
        "Mock开发模式",
        "本地模型预留",
    ]:
        assert label in text

    assert "AI Agent Admin" not in text

