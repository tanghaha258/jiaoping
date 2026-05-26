# AI Contract Copy Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Localize visible AI contract names, thinking steps, and adoption rules so the admin AI-agent page presents the local contract foundation clearly in Chinese.

**Architecture:** Keep the existing provider-neutral `AI_AGENT_CONTRACTS` structure unchanged. Update only human-facing contract text and protect it with API tests, so future GJT/local-model providers can keep using the same machine-readable fields.

**Tech Stack:** FastAPI, pytest, Pydantic schemas, Vue admin contract panel.

---

### Task 1: Contract Copy Red Test

**Files:**
- Modify: `backend/tests/test_ai_contract_progress.py`

- [x] **Step 1: Write the failing test**

Add a test that calls `/api/v1/ai/contracts` and asserts every contract has Chinese-facing `name`, `thinking_steps[].title`, and `adoption_rule`, with no known English placeholder phrases.

- [x] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest backend/tests/test_ai_contract_progress.py -q
```

Expected: FAIL because current contract copy contains English titles such as `AI lesson-plan workflow` and `Teacher adoption creates...`.

### Task 2: Localize Contract Copy

**Files:**
- Modify: `backend/app/core/ai_schemas.py`

- [x] **Step 1: Update lesson-plan thinking steps**

Translate the lesson-plan thinking step titles and descriptions into concise Chinese while preserving the existing `code` and `percent` values.

- [x] **Step 2: Update all contract names and adoption rules**

Translate contract names and adoption rules for lesson plan, learning diagnosis, rubric generation, resource recommendation, and teaching reflection.

- [x] **Step 3: Run target test**

Run:

```powershell
python -m pytest backend/tests/test_ai_contract_progress.py -q
```

Expected: PASS.

### Task 3: Verification And Progress

**Files:**
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
- Modify: `docs/superpowers/plans/2026-05-26-ai-contract-copy-polish.md`

- [x] **Step 1: Run release checks**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check-release.ps1
```

Expected: backend tests pass, backend compile passes, frontend text health passes, route smoke passes, frontend build passes.

- [x] **Step 2: Browser smoke**

Open `/admin/ai-agents`, verify the local contract panel shows Chinese thinking steps/adoption rule and no English placeholder copy in the visible contract panel.

- [ ] **Step 3: Commit and push**

Commit message: `Localize AI contract copy`

Push branch: `codex/agent-contract-crud`.
