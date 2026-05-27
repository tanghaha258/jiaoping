# AI Call Failure Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist structured AI provider failure diagnostics, expose failure summaries and filters, and link AI provider risk into trial readiness.

**Architecture:** Extend the existing provider-neutral AI call path instead of introducing a new logging subsystem. Providers return safe diagnostic metadata, `AIService` persists it on `AIAgentCall`, list/summary APIs expose it, and Vue admin pages render operational filters and diagnosis panels. Trial readiness reuses existing `DashboardService` checks with targeted AI provider risk logic.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, SQLite JSON columns, Pydantic, pytest with FastAPI `TestClient`, Vue 3, TypeScript, Element Plus, existing release scripts.

---

## File Structure

- Create `backend/tests/test_ai_call_failure_observability.py`: backend TDD coverage for failure metadata, redaction, summary, filtering, and readiness linkage.
- Modify `backend/app/services/providers/base.py`: add optional `diagnostic_metadata` to `AIProviderResult`.
- Modify `backend/app/services/providers/openai_compatible.py`: classify missing config, timeout, unreachable upstream, and malformed response failures.
- Modify `backend/app/services/ai_gateway.py`: return `provider_unsupported` instead of silently falling back to mock; classify contract validation failures.
- Modify `backend/app/models/ai_agent_call.py`: add JSON `diagnostic_metadata`.
- Modify `backend/app/services/ai_service.py`: persist diagnostics, serialize `error_category`, add list filtering and diagnostics summary service.
- Modify `backend/app/api/routers/ai.py`: add `error_category` query param and `/calls/diagnostics/summary` route.
- Modify `backend/app/services/lesson_plan_workflow.py`: persist diagnostics for the lesson-plan workflow path.
- Modify `backend/app/services/dashboard_service.py`: upgrade trial readiness AI item with provider readiness and recent failure risk.
- Modify `frontend/src/api/ai.ts`: add diagnostic metadata types and summary API.
- Modify `frontend/src/api/admin.ts`: pass `error_category` to AI call list.
- Modify `frontend/src/views/admin/AICallHistory.vue`: render diagnostics summary, filter, category column, and drawer diagnosis panel.
- Modify `frontend/src/views/admin/AdminDashboard.vue`: ensure readiness copy supports AI provider risk states.
- Modify `backend/tests/test_ai_call_page_polish.py`: static anchors for new UI.
- Modify `backend/tests/test_frontend_route_smoke.py`: keep route smoke anchors aligned.
- Modify `docs/superpowers/progress/2026-05-25-platform-progress.md`: update stage progress after implementation.
- Modify `docs/superpowers/plans/2026-05-28-ai-call-failure-observability.md`: check off tasks as they complete.

---

### Task 1: Backend Red Tests for Diagnostics Contract

**Files:**
- Create: `backend/tests/test_ai_call_failure_observability.py`
- Modify: `docs/superpowers/plans/2026-05-28-ai-call-failure-observability.md`

- [ ] **Step 1: Write failing backend tests**

Add tests that exercise the public API and provider boundary:

```python
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import AsyncSessionFactory
from app.main import app
from app.models.ai_agent import AIAgent
from app.models.ai_agent_call import AIAgentCall
from app.services.providers.base import AIProviderRequest
from app.services.providers.openai_compatible import OpenAICompatibleProvider


def _login(client: TestClient, username: str = "admin") -> dict[str, str]:
    password = "admin123" if username == "admin" else "password"
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def _create_agent(client: TestClient, headers: dict[str, str], provider: str, config: dict) -> str:
    response = client.post(
        "/api/v1/ai/agents",
        headers=headers,
        json={
            "name": f"{provider} diagnostics agent",
            "provider": provider,
            "scenario": "lesson_plan",
            "config": {"provider": provider, **config},
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"},
            "enabled": True,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["id"]


def _call_payload(agent_id: str) -> dict:
    return {
        "agent_id": agent_id,
        "scenario": "lesson_plan",
        "input": {
            "theme": "海洋生态保护",
            "grade": "七年级",
            "subject_ids": [],
            "class_ids": [],
            "lesson_count": 2,
        },
    }


def test_ai_call_failure_persists_safe_diagnostic_metadata():
    with TestClient(app) as client:
        headers = _login(client)
        agent_id = _create_agent(
            client,
            headers,
            "qwen_agent",
            {"model": "qwen-plus", "api_key": "secret-key-for-test"},
        )

        response = client.post("/api/v1/ai/calls", headers=headers, json=_call_payload(agent_id))
        calls_response = client.get("/api/v1/ai/calls?error_category=configuration_missing", headers=headers)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["status"] == "failed"
    assert data["error_category"] == "configuration_missing"
    assert data["diagnostic_metadata"]["retryable"] is False
    assert data["diagnostic_metadata"]["provider"] == "qwen_agent"
    assert "endpoint" in data["diagnostic_metadata"]["safe_metadata"]["missing"]
    assert "secret-key-for-test" not in str(data)

    assert calls_response.status_code == 200
    items = calls_response.json()["data"]["items"]
    assert any(item["id"] == data["id"] for item in items)
    assert all(item["error_category"] == "configuration_missing" for item in items)


def test_ai_call_diagnostics_summary_groups_failed_calls():
    with TestClient(app) as client:
        headers = _login(client)
        agent_id = _create_agent(client, headers, "deepseek_agent", {"model": "deepseek-chat"})
        call_response = client.post("/api/v1/ai/calls", headers=headers, json=_call_payload(agent_id))
        summary_response = client.get("/api/v1/ai/calls/diagnostics/summary", headers=headers)

    assert call_response.status_code == 200
    assert summary_response.status_code == 200
    data = summary_response.json()["data"]
    assert data["total_failed"] >= 1
    assert any(item["category"] == "configuration_missing" for item in data["by_category"])
    assert any(item["provider"] == "deepseek_agent" for item in data["by_provider"])
    assert data["recent_failures"]
    assert data["recent_failures"][0]["error_category"]


def test_openai_compatible_provider_classifies_bad_json_and_timeout():
    class BadJsonProvider(OpenAICompatibleProvider):
        def _post_json(self, endpoint, payload, api_key, timeout):
            return {"choices": [{"message": {"content": "not json"}}]}

    provider = BadJsonProvider(provider_name="kimi_agent")
    request = AIProviderRequest(
        scenario="lesson_plan",
        input_data={"theme": "海洋生态保护"},
        user_id="00000000-0000-0000-0000-000000000001",
        school_id="00000000-0000-0000-0000-000000000002",
        agent_config={
            "endpoint": "https://example.test/v1/chat/completions",
            "model": "moonshot-v1",
            "api_key": "secret-key-for-test",
        },
    )

    result = __import__("asyncio").run(provider.run(request))

    assert result.success is False
    assert result.diagnostic_metadata["error_category"] == "upstream_bad_response"
    assert "secret-key-for-test" not in str(result.diagnostic_metadata)


def test_trial_readiness_warns_when_recent_real_provider_failure_exists():
    with TestClient(app) as client:
        headers = _login(client)
        agent_id = _create_agent(client, headers, "qwen_agent", {"model": "qwen-plus"})
        call_response = client.post("/api/v1/ai/calls", headers=headers, json=_call_payload(agent_id))
        readiness_response = client.get("/api/v1/dashboard/trial-readiness", headers=headers)

    assert call_response.status_code == 200
    assert readiness_response.status_code == 200
    ai_item = next(item for item in readiness_response.json()["data"]["items"] if item["key"] == "ai_contract")
    assert ai_item["status"] in {"error", "warning"}
    assert ai_item["route"] in {"/admin/ai-agents", "/admin/ai-calls"}
```

- [ ] **Step 2: Verify red state**

Run:

```powershell
python -m pytest backend/tests/test_ai_call_failure_observability.py -q
```

Expected: fail because `diagnostic_metadata`, `error_category`, and `/ai/calls/diagnostics/summary` do not exist yet.

- [ ] **Step 3: Commit red tests**

Run:

```powershell
git add backend/tests/test_ai_call_failure_observability.py docs/superpowers/plans/2026-05-28-ai-call-failure-observability.md
git commit -m "Add AI call failure observability red tests"
git push
```

---

### Task 2: Backend Diagnostics Persistence and Classification

**Files:**
- Modify: `backend/app/services/providers/base.py`
- Modify: `backend/app/services/providers/openai_compatible.py`
- Modify: `backend/app/services/ai_gateway.py`
- Modify: `backend/app/models/ai_agent_call.py`
- Modify: `backend/app/services/ai_service.py`
- Modify: `backend/app/api/routers/ai.py`
- Modify: `backend/app/services/lesson_plan_workflow.py`
- Modify: `docs/superpowers/plans/2026-05-28-ai-call-failure-observability.md`
- Test: `backend/tests/test_ai_call_failure_observability.py`

- [ ] **Step 1: Add provider result diagnostics field**

Update `AIProviderResult`:

```python
diagnostic_metadata: dict[str, Any] = field(default_factory=dict)
```

- [ ] **Step 2: Add call persistence field**

Add to `AIAgentCall`:

```python
diagnostic_metadata = Column(JSON, nullable=True, default=dict)
```

- [ ] **Step 3: Implement diagnostic helpers in `AIService`**

Add helpers that normalize a metadata object with:

```python
{
    "error_code": category,
    "error_category": category,
    "provider": provider,
    "scenario": scenario,
    "retryable": retryable,
    "remediation": remediation,
    "upstream_status": upstream_status,
    "safe_metadata": safe_metadata,
}
```

The helpers must redact keys containing `key`, `token`, `secret`, `authorization`, or `password`.

- [ ] **Step 4: Persist diagnostics for normal AI calls**

In `AIService.initiate_call`, when `provider_result.success` is false:

```python
call.status = "failed"
call.error_message = provider_result.error_message
call.diagnostic_metadata = self._diagnostic_from_provider_result(provider_result, agent.provider, scenario)
```

In the exception path, persist `unknown_error`.

- [ ] **Step 5: Classify OpenAI-compatible provider failures**

Update `_failure` in `OpenAICompatibleProvider` to accept `category`, `retryable`, and `safe_metadata`. Use:

- missing config -> `configuration_missing`, retryable false;
- URL/connection -> `upstream_unreachable`, retryable true;
- timeout -> `upstream_timeout`, retryable true;
- malformed JSON or missing content -> `upstream_bad_response`, retryable false.

- [ ] **Step 6: Stop unsupported provider fallback**

In `AIGateway.execute`, if provider is missing, return failed `AIProviderResult` with category `provider_unsupported` instead of executing mock.

- [ ] **Step 7: Classify output contract validation**

When `validate_output` fails, set diagnostic metadata category `contract_validation_failed`.

- [ ] **Step 8: Persist diagnostics for lesson-plan workflow**

In `LessonPlanWorkflowService.create_draft`, failed provider results and caught exceptions should set `call.diagnostic_metadata` before raising `AIProviderUnavailableException`.

- [ ] **Step 9: Serialize error category**

Update `_call_to_dict` to include:

```python
"diagnostic_metadata": call.diagnostic_metadata or {},
"error_category": (call.diagnostic_metadata or {}).get("error_category"),
```

- [ ] **Step 10: Add diagnostics summary and filter**

Add `AIService.get_call_diagnostics_summary(...)`, filtering by school like `list_calls`, and add `error_category` to list filters.

Add router support:

```python
@router.get("/calls/diagnostics/summary")
async def get_call_diagnostics_summary(...):
    ...
```

Place this route before `@router.get("/calls/{call_id}")`.

- [ ] **Step 11: Verify backend green**

Run:

```powershell
python -m pytest backend/tests/test_ai_call_failure_observability.py backend/tests/test_ai_provider_readiness.py backend/tests/test_domestic_provider_contract.py -q
python -m compileall backend\app
```

Expected: all tests pass and compile succeeds.

- [ ] **Step 12: Commit backend implementation**

Run:

```powershell
git add backend/app backend/tests/test_ai_call_failure_observability.py docs/superpowers/plans/2026-05-28-ai-call-failure-observability.md
git commit -m "Persist AI call failure diagnostics"
git push
```

---

### Task 3: Trial Readiness AI Provider Risk Linkage

**Files:**
- Modify: `backend/app/services/dashboard_service.py`
- Modify: `backend/tests/test_ai_call_failure_observability.py`
- Modify: `docs/superpowers/plans/2026-05-28-ai-call-failure-observability.md`

- [ ] **Step 1: Extend readiness logic**

Update `_ai_contract_item` to inspect:

- enabled `lesson_plan` agents;
- readiness blockers for real providers with missing endpoint/model/key;
- recent real-provider failed calls.

Keep `mock` acceptable for local trial readiness unless a real provider is configured and broken.

- [ ] **Step 2: Verify readiness test passes**

Run:

```powershell
python -m pytest backend/tests/test_ai_call_failure_observability.py::test_trial_readiness_warns_when_recent_real_provider_failure_exists backend/tests/test_trial_readiness.py -q
```

Expected: all selected readiness tests pass.

- [ ] **Step 3: Commit readiness linkage**

Run:

```powershell
git add backend/app/services/dashboard_service.py backend/tests/test_ai_call_failure_observability.py docs/superpowers/plans/2026-05-28-ai-call-failure-observability.md
git commit -m "Link AI provider diagnostics to trial readiness"
git push
```

---

### Task 4: Frontend Diagnostics UI

**Files:**
- Modify: `frontend/src/api/ai.ts`
- Modify: `frontend/src/api/admin.ts`
- Modify: `frontend/src/views/admin/AICallHistory.vue`
- Modify: `backend/tests/test_ai_call_page_polish.py`
- Modify: `backend/tests/test_frontend_route_smoke.py`
- Modify: `docs/superpowers/plans/2026-05-28-ai-call-failure-observability.md`

- [ ] **Step 1: Write failing frontend static anchors**

Extend `test_ai_call_page_polish.py` to require:

```python
"失败诊断"
"失败类别"
"可重试"
"处理建议"
"近期失败"
"diagnostic_metadata"
"getAICallDiagnosticsSummary"
```

- [ ] **Step 2: Verify red state**

Run:

```powershell
python -m pytest backend/tests/test_ai_call_page_polish.py -q
```

Expected: fail because the page and API types do not contain the new diagnostics anchors yet.

- [ ] **Step 3: Add TypeScript API types and call**

Extend `AICallItem` and add:

```ts
export interface AICallDiagnosticMetadata {
  error_code?: string
  error_category?: string
  provider?: string
  scenario?: string
  retryable?: boolean
  remediation?: string
  upstream_status?: string | number | null
  safe_metadata?: Record<string, any>
}

export interface AICallDiagnosticsSummary {
  total_failed: number
  by_category: { category: string; count: number }[]
  by_provider: { provider: string; count: number }[]
  recent_failures: {
    id: string
    provider: string
    scenario: string
    error_category: string
    error_message?: string | null
    created_at?: string | null
  }[]
}

export function getAICallDiagnosticsSummary(): Promise<ApiResponse<AICallDiagnosticsSummary>> {
  return request.get('/ai/calls/diagnostics/summary')
}
```

- [ ] **Step 4: Add admin list filter param**

Extend `getAdminAICalls` params with:

```ts
error_category?: string
```

- [ ] **Step 5: Render AI call diagnostics UI**

Update `AICallHistory.vue`:

- load diagnostics summary alongside calls;
- add error category select filter;
- add failure category column;
- add summary cards for total failures, top failure category, affected providers, and recent failures;
- replace drawer plain error alert with a diagnosis panel showing category, retryable, remediation, upstream status, and safe metadata.

- [ ] **Step 6: Verify frontend static and build**

Run:

```powershell
python -m pytest backend/tests/test_ai_call_page_polish.py backend/tests/test_frontend_route_smoke.py backend/tests/test_frontend_text_health.py -q
cd frontend
npm run build
cd ..
```

Expected: tests and build pass.

- [ ] **Step 7: Commit frontend UI**

Run:

```powershell
git add frontend/src/api frontend/src/views/admin/AICallHistory.vue backend/tests/test_ai_call_page_polish.py backend/tests/test_frontend_route_smoke.py docs/superpowers/plans/2026-05-28-ai-call-failure-observability.md
git commit -m "Add AI call diagnostics UI"
git push
```

---

### Task 5: Release Verification, Browser Smoke, and Progress Update

**Files:**
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
- Modify: `docs/superpowers/plans/2026-05-28-ai-call-failure-observability.md`

- [ ] **Step 1: Run full release verification**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check-release.ps1
```

Expected: backend tests, backend compile, frontend text health, route smoke, and frontend build all pass.

- [ ] **Step 2: Browser smoke**

If local services are available, open:

- `http://127.0.0.1:3000/admin/ai-calls`
- `http://127.0.0.1:3000/admin`

Expected: AI call diagnostics labels render, and Dashboard readiness still renders without overlap.

- [ ] **Step 3: Update progress**

Update `docs/superpowers/progress/2026-05-25-platform-progress.md` to mark P10 Batch 3 implementation complete and record verification evidence.

- [ ] **Step 4: Commit verification checkpoint**

Run:

```powershell
git add docs/superpowers/progress/2026-05-25-platform-progress.md docs/superpowers/plans/2026-05-28-ai-call-failure-observability.md
git commit -m "Verify AI call failure observability"
git push
```

---

## Self-Review

- Spec coverage: structured metadata, classification, persistence, summary API, list filtering, frontend diagnosis UI, Dashboard readiness linkage, and release verification are each mapped to tasks.
- Unfinished-marker scan: no unresolved planning markers are intentionally left.
- Type consistency: `diagnostic_metadata`, `error_category`, and `getAICallDiagnosticsSummary` are used consistently across backend, frontend, and tests.
