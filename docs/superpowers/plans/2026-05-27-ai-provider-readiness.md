# AI Provider Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only AI agent provider readiness check so administrators can see whether each configured agent is ready, missing configuration, manual-only, or unsupported.

**Architecture:** Keep provider execution unchanged. Add a local readiness evaluator in `AIService`, expose it through `/api/v1/ai/agents/{agent_id}/readiness`, and render the result in the AI agent governance page. The check validates local config only and never calls an upstream model.

**Tech Stack:** FastAPI, SQLAlchemy async, pytest, Vue 3, Element Plus, TypeScript.

---

### Task 1: Backend Readiness TDD

**Files:**
- Create: `backend/tests/test_ai_provider_readiness.py`
- Modify later: `backend/app/services/ai_service.py`
- Modify later: `backend/app/api/routers/ai.py`

- [x] **Step 0: Protect system-admin AI agent management**

Assert the seeded `system_admin` account can create test AI agents because the admin UI is primarily used through `admin/admin123`.

- [x] **Step 1: Write tests for readiness statuses**

Create tests that:

- create a `mock` agent and assert status `ready`;
- create an `openai_compatible_local` agent missing endpoint/key and assert status `not_configured`;
- create an `openai_compatible_local` agent with endpoint/model/api_key_env and a real test env var and assert status `ready`;
- create a `manual_import` agent and assert status `manual_required`;
- create an agent then patch provider in DB to `unknown_provider` and assert status `unsupported`.

- [x] **Step 2: Write tests for HTTP and role behavior**

Assert:

- system admin can call `GET /api/v1/ai/agents/{agent_id}/readiness`;
- school admin can call the same endpoint;
- teacher gets 403;
- missing agent returns 404-style error response.

- [x] **Step 3: Run red test**

Run:

```powershell
python -m pytest backend/tests/test_ai_provider_readiness.py -q
```

Expected: fails with 404 or missing method.

Observed 2026-05-27: `python -m pytest backend/tests/test_ai_provider_readiness.py -q` failed with 4 failures because `GET /api/v1/ai/agents/{agent_id}/readiness` returned 404. This confirms the red state for the missing readiness endpoint.

### Task 2: Backend Implementation

**Files:**
- Modify: `backend/app/services/ai_service.py`
- Modify: `backend/app/api/routers/ai.py`

- [ ] **Step 1: Add readiness evaluator**

Add `AIService.get_agent_readiness(db, agent_id, user)` returning:

- `agent_id`
- `provider`
- `status`
- `mode`
- `label`
- `summary`
- `checks[]`
- `actions[]`

- [ ] **Step 2: Implement provider rules**

Rules:

- `mock`: ready.
- `gjt_api`: endpoint and agent id are required; key is warning.
- domestic/OpenAI-compatible providers: endpoint, model, and key source are required.
- `gjt_link` and `manual_import`: manual_required.
- unknown provider: unsupported.

- [ ] **Step 3: Add route**

Add:

```python
@router.get("/agents/{agent_id}/readiness")
async def get_agent_readiness(...):
    current_user = Depends(require_roles("system_admin", "school_admin", "admin", "super_admin"))
```

- [ ] **Step 4: Run backend green test**

Run:

```powershell
python -m pytest backend/tests/test_ai_provider_readiness.py -q
```

Expected: pass.

### Task 3: Frontend Readiness UI

**Files:**
- Modify: `frontend/src/api/ai.ts`
- Modify: `frontend/src/views/admin/AIAgentConfig.vue`
- Modify: `backend/tests/test_ai_agent_page_polish.py`

- [ ] **Step 1: Extend frontend static test**

Add required copy anchors:

- `配置自检`
- `配置可运行`
- `缺少配置`
- `需要人工回填`
- `接口端点`
- `模型标识`
- `密钥来源`
- `环境变量未设置`

- [ ] **Step 2: Run red frontend static test**

Run:

```powershell
python -m pytest backend/tests/test_ai_agent_page_polish.py -q
```

Expected: fail until the page is updated.

- [ ] **Step 3: Add API type and function**

Add:

```ts
export interface AIAgentReadiness { ... }
export function getAgentReadiness(id: string): Promise<ApiResponse<AIAgentReadiness>>
```

- [ ] **Step 4: Render readiness in AI agent page**

Add:

- readiness column;
- row-level self-check button;
- detail drawer readiness panel;
- loading state for each checked agent;
- fallback text before check is run.

- [ ] **Step 5: Run frontend targeted checks**

Run:

```powershell
python -m pytest backend/tests/test_ai_agent_page_polish.py backend/tests/test_frontend_route_smoke.py backend/tests/test_frontend_text_health.py -q
cd frontend
npm run build
```

Expected: pass.

### Task 4: Verify, Browser Smoke, Commit, Push

**Files:**
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
- Modify: `docs/superpowers/plans/2026-05-27-ai-provider-readiness.md`

- [ ] **Step 1: Run release check**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check-release.ps1
```

Expected: backend tests, compile, frontend text health, route smoke, and frontend build pass.

- [ ] **Step 2: Browser smoke**

Open:

```text
http://127.0.0.1:3000/admin/ai-agents
```

Verify visible copy:

- `配置自检`
- `配置可运行`
- row-level self-check action

- [ ] **Step 3: Update progress and plan**

Record verification and browser smoke results.

- [ ] **Step 4: Commit and push**

Run:

```powershell
git diff --check
git add backend/app backend/tests frontend/src docs
git commit -m "Add AI provider readiness checks"
git push origin codex/agent-contract-crud
```
