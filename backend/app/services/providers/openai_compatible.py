"""OpenAI-compatible provider adapter for domestic model gateways."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib import request as urlrequest
from urllib.error import URLError

from app.core.config import settings
from app.services.providers.base import BaseAIProvider, AIProviderRequest, AIProviderResult


class OpenAICompatibleProvider(BaseAIProvider):
    """JSON-focused adapter for OpenAI-compatible domestic AI endpoints."""

    provider_name = "openai_compatible_local"

    def __init__(self, provider_name: str | None = None):
        if provider_name:
            self.provider_name = provider_name

    async def run(self, request: AIProviderRequest) -> AIProviderResult:
        config = request.agent_config or {}
        endpoint = config.get("endpoint") or settings.OPENAI_COMPATIBLE_API_BASE_URL
        model = config.get("model") or settings.OPENAI_COMPATIBLE_MODEL
        api_key = self._resolve_api_key(config)
        timeout = int(
            config.get("timeout_seconds")
            or settings.OPENAI_COMPATIBLE_TIMEOUT_SECONDS
            or 60
        )

        missing = [
            name
            for name, value in {
                "endpoint": endpoint,
                "model": model,
                "api_key": api_key,
            }.items()
            if not value
        ]
        if missing:
            return self._failure(
                request,
                f"Missing OpenAI-compatible provider config: {', '.join(missing)}",
                "configuration_missing",
                retryable=False,
                safe_metadata={"missing": missing, "model": model},
            )

        payload = self._build_payload(request, model, config)

        try:
            response = await asyncio.to_thread(
                self._post_json,
                endpoint,
                payload,
                api_key,
                timeout,
            )
            content = self._extract_content(response)
        except TimeoutError as exc:
            return self._failure(
                request,
                str(exc),
                "upstream_timeout",
                retryable=True,
                safe_metadata={"model": model, "timeout_seconds": timeout},
            )
        except URLError as exc:
            return self._failure(
                request,
                str(exc),
                "upstream_unreachable",
                retryable=True,
                safe_metadata={"model": model},
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return self._failure(
                request,
                str(exc),
                "upstream_bad_response",
                retryable=False,
                safe_metadata={"model": model},
            )

        return AIProviderResult(
            success=True,
            content=content,
            provider=self.provider_name,
            scenario=request.scenario,
            metadata={
                "upstream": self.provider_name,
                "model": model,
                "usage": response.get("usage") if isinstance(response, dict) else None,
            },
            requires_review=True,
            finished_at=datetime.now(timezone.utc),
        )

    async def health_check(self) -> bool:
        return bool(settings.OPENAI_COMPATIBLE_API_BASE_URL and settings.OPENAI_COMPATIBLE_MODEL)

    def _resolve_api_key(self, config: dict[str, Any]) -> str:
        api_key_env = config.get("api_key_env")
        if api_key_env:
            return os.getenv(api_key_env, "")
        return config.get("api_key") or settings.OPENAI_COMPATIBLE_API_KEY

    def _build_payload(self, request: AIProviderRequest, model: str, config: dict[str, Any]) -> dict[str, Any]:
        extra = config.get("extra") or {}
        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": self._system_prompt(request.scenario),
                },
                {
                    "role": "user",
                    "content": json.dumps(request.input_data, ensure_ascii=False),
                },
            ],
            "response_format": {"type": "json_object"},
            "temperature": extra.get("temperature", 0.4),
        }
        for key in ("top_p", "max_tokens"):
            if key in extra:
                payload[key] = extra[key]
        return payload

    def _system_prompt(self, scenario: str) -> str:
        base = (
            "你是“跨学科教学评一体化平台”的结构化教学智能体。"
            "你必须只输出 JSON，不要输出 Markdown、解释文字或代码块。"
            "输出只供教师审阅采纳，不能直接发布给学生。"
        )
        if scenario == "lesson_plan":
            return (
                base
                + "必须包含 project、tasks、rubric、resources、teacher_notes 五个顶层字段。"
                + "tasks 表示草稿任务，不要写已发布。"
            )
        return base

    def _post_json(self, endpoint: str, payload: dict[str, Any], api_key: str, timeout: int) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        req = urlrequest.Request(endpoint, data=body, headers=headers, method="POST")
        with urlrequest.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("OpenAI-compatible response must be a JSON object")
        return parsed

    def _extract_content(self, response: dict[str, Any]) -> Any:
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("OpenAI-compatible response missing choices")
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise ValueError("OpenAI-compatible response missing message content")
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"OpenAI-compatible response content is not valid JSON: {exc}") from exc

    def _failure(
        self,
        request: AIProviderRequest,
        message: str,
        category: str,
        retryable: bool = False,
        safe_metadata: dict[str, Any] | None = None,
    ) -> AIProviderResult:
        return AIProviderResult(
            success=False,
            content=None,
            provider=self.provider_name,
            scenario=request.scenario,
            error_message=message,
            diagnostic_metadata={
                "error_code": category,
                "error_category": category,
                "provider": self.provider_name,
                "scenario": request.scenario,
                "retryable": retryable,
                "remediation": self._remediation(category),
                "upstream_status": None,
                "safe_metadata": safe_metadata or {},
            },
            requires_review=True,
            finished_at=datetime.now(timezone.utc),
        )

    def _remediation(self, category: str) -> str:
        mapping = {
            "configuration_missing": "补齐 Provider endpoint、model 和 api_key_env 后重新发起调用。",
            "upstream_unreachable": "检查 Provider endpoint、网络连通性和服务可用性后重试。",
            "upstream_timeout": "检查 Provider 响应时间，必要时调大 timeout_seconds 后重试。",
            "upstream_bad_response": "检查上游返回是否为合法 JSON，并确认模型按本地契约输出。",
        }
        return mapping.get(category, "查看 Provider 配置和调用记录后处理。")
