"""Deployment smoke test for the teaching-assessment platform.

Environment:
    JIAOPING_API_BASE=http://127.0.0.1:8000/api/v1
    JIAOPING_SMOKE_USERNAME=teacher001
    JIAOPING_SMOKE_PASSWORD=password
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_BASE = os.environ.get("JIAOPING_API_BASE", "http://127.0.0.1:8000/api/v1").rstrip("/")
USERNAME = os.environ.get("JIAOPING_SMOKE_USERNAME", "teacher001")
PASSWORD = os.environ.get("JIAOPING_SMOKE_PASSWORD", "password")


@dataclass
class SmokeResult:
    name: str
    ok: bool
    detail: str


def request_json(path: str, method: str = "GET", body: dict[str, Any] | None = None, token: str | None = None) -> dict[str, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(f"{API_BASE}{path}", data=data, headers=headers, method=method)
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def run_check(name: str, fn) -> SmokeResult:
    try:
        detail = fn()
        return SmokeResult(name=name, ok=True, detail=detail)
    except HTTPError as exc:
        return SmokeResult(name=name, ok=False, detail=f"HTTP {exc.code}: {exc.read().decode('utf-8', 'ignore')}")
    except URLError as exc:
        return SmokeResult(name=name, ok=False, detail=f"connection failed: {exc.reason}")
    except Exception as exc:  # pragma: no cover - smoke script runtime safety
        return SmokeResult(name=name, ok=False, detail=str(exc))


def check_liveness() -> str:
    payload = request_json("/health")
    data = payload["data"]
    if data["status"] != "ok":
        raise RuntimeError(f"unexpected liveness status: {data}")
    return f"{data['service']} {data['version']} {data['environment']}"


def check_readiness() -> str:
    payload = request_json("/health/ready")
    data = payload["data"]
    if data["status"] != "ready":
        raise RuntimeError(json.dumps(data, ensure_ascii=False))
    return json.dumps(data["checks"], ensure_ascii=False)


def check_ai_contracts() -> str:
    login = request_json(
        "/auth/login",
        method="POST",
        body={"username": USERNAME, "password": PASSWORD},
    )
    token = login["data"]["access_token"]
    contracts = request_json("/ai/contracts", token=token)
    scenarios = [item["scenario"] for item in contracts["data"]["items"]]
    if "lesson_plan" not in scenarios:
        raise RuntimeError(f"lesson_plan contract missing: {scenarios}")
    return f"contracts={','.join(scenarios)}"


def main() -> int:
    checks = [
        run_check("health", check_liveness),
        run_check("readiness", check_readiness),
        run_check("ai_contracts", check_ai_contracts),
    ]
    print(json.dumps([check.__dict__ for check in checks], ensure_ascii=False, indent=2))
    return 0 if all(check.ok for check in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
