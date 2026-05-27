"""Guangxi JiaoTong API provider placeholder.

The exact upstream contract can be adjusted here when the official document is
available. The rest of the teaching workflow consumes the same normalized JSON
draft and does not need to change.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any
from urllib import request as urlrequest
from urllib.error import URLError

from app.core.config import settings
from app.services.providers.base import BaseAIProvider, AIProviderRequest, AIProviderResult


class GjtApiProvider(BaseAIProvider):
    """Minimal JSON-over-HTTP provider for future GJT agent integration."""

    provider_name = "gjt_api"

    async def run(self, request: AIProviderRequest) -> AIProviderResult:
        endpoint = request.agent_config.get("endpoint") or settings.GJT_API_BASE_URL
        api_key = request.agent_config.get("api_key") or settings.GJT_API_KEY
        agent_id = request.agent_config.get("agent_id") or settings.GJT_AGENT_ID
        timeout = int(request.agent_config.get("timeout_seconds") or settings.GJT_API_TIMEOUT_SECONDS)

        missing = [name for name, value in {"endpoint": endpoint, "agent_id": agent_id}.items() if not value]
        if missing:
            return self._failure(
                request,
                f"Missing GJT provider config: {', '.join(missing)}",
                "configuration_missing",
                retryable=False,
                safe_metadata={"missing": missing, "agent_id": agent_id},
            )

        payload = {
            "agent_id": agent_id,
            "scenario": request.scenario,
            "input": request.input_data,
            "output_format": "json",
        }

        try:
            response = await asyncio.to_thread(
                self._post_json,
                endpoint,
                payload,
                api_key,
                timeout,
            )
        except TimeoutError as exc:
            return self._failure(request, str(exc), "upstream_timeout", retryable=True, safe_metadata={"agent_id": agent_id})
        except URLError as exc:
            return self._failure(request, str(exc), "upstream_unreachable", retryable=True, safe_metadata={"agent_id": agent_id})
        except (OSError, ValueError) as exc:
            return self._failure(request, str(exc), "upstream_bad_response", retryable=False, safe_metadata={"agent_id": agent_id})

        content = response.get("draft") or response.get("content") or response.get("data") or response
        return AIProviderResult(
            success=True,
            content=content,
            provider=self.provider_name,
            scenario=request.scenario,
            metadata={"upstream": "gjt_api", "agent_id": agent_id},
            requires_review=True,
            finished_at=datetime.now(timezone.utc),
        )

    async def health_check(self) -> bool:
        return bool(settings.GJT_API_BASE_URL)

    def _post_json(self, endpoint: str, payload: dict[str, Any], api_key: str, timeout: int) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        req = urlrequest.Request(endpoint, data=body, headers=headers, method="POST")
        with urlrequest.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("GJT API response must be a JSON object")
        return parsed

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
            "configuration_missing": "补齐桂教通 endpoint、agent_id 和鉴权配置后重新自检。",
            "upstream_unreachable": "检查桂教通地址、网络、白名单和服务状态。",
            "upstream_timeout": "检查桂教通响应时间，必要时调大 timeout_seconds 后重试。",
            "upstream_bad_response": "检查桂教通返回是否为合法 JSON，并确认智能体输出契约。",
        }
        return mapping.get(category, "查看桂教通 Provider 配置和调用记录后处理。")
