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
        "OpenAI兼容本地网关",
        "通义千问",
        "DeepSeek",
        "智谱GLM",
        "豆包",
        "百度千帆",
        "讯飞星火",
        "Kimi",
        "国内智能体预设",
        "配置自检",
        "配置可运行",
        "缺少配置",
        "需要人工回填",
        "接口端点",
        "模型标识",
        "密钥来源",
        "环境变量未设置",
    ]:
        assert label in text

    assert "AI Agent Admin" not in text
