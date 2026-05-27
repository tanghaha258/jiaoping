# Domestic AI Provider Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Phase 10 provider-neutral AI infrastructure so the platform can use 桂教通 or domestic OpenAI-compatible AI agents through the same local teaching workflow contracts.

**Architecture:** Keep business workflows unchanged. Extend provider identifiers and admin configuration copy, add a reusable OpenAI-compatible provider adapter, register domestic provider aliases in `AIGateway`, and document the manual 桂教通 agent prompt. Providers return `AIProviderResult`; lesson-plan workflow still normalizes drafts and requires teacher adoption.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy async, pytest, Vue 3, Element Plus, TypeScript.

---

### Task 1: Lock Provider Contract With TDD

**Files:**
- Create: `backend/tests/test_domestic_provider_contract.py`
- Modify later: `backend/app/core/ai_schemas.py`
- Modify later: `backend/app/services/ai_service.py`
- Modify later: `backend/app/services/ai_gateway.py`
- Create later: `backend/app/services/providers/openai_compatible.py`

- [x] **Step 1: Write failing tests for provider identifiers and gateway registration**

Create tests that assert:

- `AIAgentCreate` accepts `openai_compatible_local`, `qwen_agent`, `deepseek_agent`, `zhipu_agent`, `doubao_agent`, `qianfan_agent`, `spark_agent`, and `kimi_agent`.
- `AIAgentCreate` still rejects unsupported provider names.
- `AI_AGENT_CONTRACTS` lists domestic provider modes for `lesson_plan`.
- `AIGateway().get_available_providers()` contains the domestic aliases.

- [x] **Step 2: Write failing tests for OpenAI-compatible adapter**

Test:

- missing endpoint/model/key returns failed result.
- a fake `_post_json` response with `choices[0].message.content` JSON is parsed into `content`.
- malformed JSON returns failed result.
- metadata never includes raw API key.

- [x] **Step 3: Run red tests**

Run:

```powershell
python -m pytest backend/tests/test_domestic_provider_contract.py -q
```

Expected: fail because the provider enum, gateway aliases, and adapter do not exist yet.

### Task 2: Implement Backend Provider Contract

**Files:**
- Modify: `backend/app/core/ai_schemas.py`
- Modify: `backend/app/services/ai_service.py`
- Modify: `backend/app/services/providers/base.py`
- Create: `backend/app/services/providers/openai_compatible.py`
- Modify: `backend/app/services/providers/__init__.py`
- Modify: `backend/app/services/ai_gateway.py`
- Modify: `backend/.env.example`
- Modify: `docs/DEPLOYMENT.md`

- [x] **Step 1: Add provider constants**

Create or centralize the provider list so schemas, service validation, and gateway registration use the same values.

- [x] **Step 2: Extend Pydantic provider validation**

Update `AgentConfig`, `AIAgentCreate`, and `AIAgentUpdate` provider patterns to accept domestic providers.

- [x] **Step 3: Add OpenAI-compatible provider**

Implement a provider that:

- reads endpoint/model/key from config/env;
- builds chat-completions payload;
- asks for JSON output;
- extracts and parses `choices[0].message.content`;
- returns `AIProviderResult`;
- never exposes raw keys.

- [x] **Step 4: Register domestic aliases in gateway**

Map `openai_compatible_local`, `qwen_agent`, `deepseek_agent`, `zhipu_agent`, `doubao_agent`, `qianfan_agent`, `spark_agent`, and `kimi_agent` to the reusable provider instance or provider-specific preset wrappers.

- [x] **Step 5: Update docs/env examples**

Add `DOMESTIC_AI_*` or `OPENAI_COMPATIBLE_*` env examples and note that real keys stay out of git.

- [x] **Step 6: Run green backend tests**

Run:

```powershell
python -m pytest backend/tests/test_domestic_provider_contract.py -q
```

Expected: pass.

### Task 3: Update Admin Provider Configuration UI

**Files:**
- Modify: `frontend/src/api/ai.ts`
- Modify: `frontend/src/views/admin/AIAgentConfig.vue`
- Modify: `backend/tests/test_ai_agent_page_polish.py`
- Modify: `backend/tests/test_frontend_route_smoke.py` if needed

- [x] **Step 1: Write/extend static copy test**

Assert `AIAgentConfig.vue` contains:

- `OpenAI兼容本地网关`
- `通义千问`
- `DeepSeek`
- `智谱GLM`
- `豆包`
- `百度千帆`
- `讯飞星火`
- `Kimi`
- `教师采纳门槛`

- [x] **Step 2: Run red frontend static test**

Run:

```powershell
python -m pytest backend/tests/test_ai_agent_page_polish.py -q
```

Expected: fail until page copy/options are updated.

- [x] **Step 3: Update TypeScript provider union and options**

Add the domestic provider values to `frontend/src/api/ai.ts` and the admin page provider option list.

- [x] **Step 4: Add provider guidance copy**

Explain that domestic providers are adapter presets and that secrets should be stored through backend env variables.

- [x] **Step 5: Run green targeted checks**

Run:

```powershell
python -m pytest backend/tests/test_ai_agent_page_polish.py backend/tests/test_frontend_route_smoke.py backend/tests/test_frontend_text_health.py -q
```

Expected: pass.

### Task 4: Verify, Browser Smoke, Commit, Push

**Files:**
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
- Modify: `docs/superpowers/plans/2026-05-27-domestic-provider-contract.md`

- [x] **Step 1: Run full release check**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check-release.ps1
```

Expected: backend tests, compile, text health, route smoke, and frontend build pass.

- [x] **Step 2: Browser smoke admin AI agents**

Open:

```text
http://127.0.0.1:3000/admin/ai-agents
```

Verify provider options and guidance copy render.

- [x] **Step 3: Update progress**

Record Phase 10 Batch 1 results and note that 桂教通 manual prompt is in the design doc.

- [ ] **Step 4: Commit and push**

Run:

```powershell
git diff --check
git add backend/app backend/tests frontend/src docs scripts backend/.env.example
git commit -m "Add domestic AI provider contract foundation"
git push origin codex/agent-contract-crud
```
