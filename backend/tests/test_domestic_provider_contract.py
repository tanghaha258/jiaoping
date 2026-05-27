import asyncio

import pytest
from pydantic import ValidationError

from app.core.ai_schemas import AIAgentCreate, AI_AGENT_CONTRACTS
from app.services.ai_gateway import AIGateway
from app.services.providers.base import AIProviderRequest
from app.services.providers.openai_compatible import OpenAICompatibleProvider


DOMESTIC_PROVIDERS = [
    "openai_compatible_local",
    "qwen_agent",
    "deepseek_agent",
    "zhipu_agent",
    "doubao_agent",
    "qianfan_agent",
    "spark_agent",
    "kimi_agent",
]


def _agent_payload(provider: str) -> dict:
    return {
        "name": f"{provider} test agent",
        "provider": provider,
        "scenario": "lesson_plan",
        "config": {
            "provider": provider,
            "endpoint": "https://example.test/v1/chat/completions",
            "model": "demo-model",
            "api_key_env": "DOMESTIC_AI_API_KEY",
        },
        "enabled": True,
    }


def test_ai_agent_schema_accepts_domestic_provider_identifiers():
    for provider in DOMESTIC_PROVIDERS:
        agent = AIAgentCreate(**_agent_payload(provider))
        assert agent.provider == provider
        assert agent.config.provider == provider


def test_ai_agent_schema_rejects_unknown_provider_identifier():
    payload = _agent_payload("unknown_vendor")

    with pytest.raises(ValidationError):
        AIAgentCreate(**payload)


def test_lesson_plan_contract_lists_domestic_provider_modes():
    lesson_contract = next(item for item in AI_AGENT_CONTRACTS if item["scenario"] == "lesson_plan")

    for provider in ["mock", "gjt_api", *DOMESTIC_PROVIDERS]:
        assert provider in lesson_contract["provider_modes"]


def test_gateway_registers_domestic_provider_aliases():
    providers = set(AIGateway().get_available_providers())

    for provider in ["mock", "gjt_api", *DOMESTIC_PROVIDERS]:
        assert provider in providers


def _provider_request(config: dict) -> AIProviderRequest:
    return AIProviderRequest(
        scenario="lesson_plan",
        input_data={"theme": "海洋生态保护", "grade": "七年级"},
        user_id="00000000-0000-0000-0000-000000000001",
        school_id="00000000-0000-0000-0000-000000000002",
        agent_config=config,
    )


def test_openai_compatible_provider_requires_endpoint_model_and_key():
    provider = OpenAICompatibleProvider(provider_name="deepseek_agent")

    result = asyncio.run(provider.run(_provider_request({"provider": "deepseek_agent"})))

    assert result.success is False
    assert "endpoint" in result.error_message
    assert result.requires_review is True


def test_openai_compatible_provider_parses_json_content_without_leaking_key():
    class FakeProvider(OpenAICompatibleProvider):
        def _post_json(self, endpoint, payload, api_key, timeout):
            self.seen_payload = payload
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"project":{"name":"海洋生态保护"},"tasks":[],"rubric":{},"resources":[],"teacher_notes":[]}'
                        }
                    }
                ],
                "usage": {"total_tokens": 123},
            }

    provider = FakeProvider(provider_name="qwen_agent")
    result = asyncio.run(
        provider.run(
            _provider_request(
                {
                    "provider": "qwen_agent",
                    "endpoint": "https://example.test/v1/chat/completions",
                    "api_key": "secret-key-for-test",
                    "model": "qwen-plus",
                    "timeout_seconds": 12,
                }
            )
        )
    )

    assert result.success is True
    assert result.provider == "qwen_agent"
    assert result.content["project"]["name"] == "海洋生态保护"
    assert result.metadata["upstream"] == "qwen_agent"
    assert result.metadata["model"] == "qwen-plus"
    assert "secret-key-for-test" not in str(result.metadata)
    assert provider.seen_payload["model"] == "qwen-plus"
    assert provider.seen_payload["response_format"] == {"type": "json_object"}
    assert provider.seen_payload["messages"][0]["role"] == "system"


def test_openai_compatible_provider_rejects_malformed_json_content():
    class BadJsonProvider(OpenAICompatibleProvider):
        def _post_json(self, endpoint, payload, api_key, timeout):
            return {"choices": [{"message": {"content": "not json"}}]}

    provider = BadJsonProvider(provider_name="kimi_agent")
    result = asyncio.run(
        provider.run(
            _provider_request(
                {
                    "provider": "kimi_agent",
                    "endpoint": "https://example.test/v1/chat/completions",
                    "api_key": "secret-key-for-test",
                    "model": "moonshot-v1",
                }
            )
        )
    )

    assert result.success is False
    assert "JSON" in result.error_message
    assert result.requires_review is True
