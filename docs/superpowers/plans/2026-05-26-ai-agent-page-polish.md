# AI Agent Management Page Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish the admin AI agent page so it reads as a real provider-neutral AI contract governance console, not only a raw CRUD table.

**Architecture:** Keep the existing backend APIs and data model. Improve the Vue page copy, hierarchy, summary cards, provider guidance, contract preview, detail drawer, and form guidance. Add static regression tests so key governance labels remain visible and route smoke keeps the page anchored.

**Tech Stack:** Vue 3, Element Plus, TypeScript, Python static smoke scripts, pytest.

---

### Task 1: Lock Page Copy With Failing Tests

**Files:**
- Create: `backend/tests/test_ai_agent_page_polish.py`
- Modify: `scripts/check_frontend_route_smoke.py`

- [x] **Step 1: Write the failing test**

Add a pytest file that reads `frontend/src/views/admin/AIAgentConfig.vue` as UTF-8 and asserts the page contains these admin-facing anchors:

```python
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
```

- [x] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest backend/tests/test_ai_agent_page_polish.py -q
```

Expected: FAIL because the current page still uses `AI Agent Admin` and lacks the new governance anchors.

- [x] **Step 3: Extend route smoke anchors**

In `scripts/check_frontend_route_smoke.py`, update the `ai-agents` route anchors to include `AI智能体治理`, `本地契约层`, and `Provider适配`.

- [x] **Step 4: Run route smoke to verify red state**

Run:

```powershell
python -m pytest backend/tests/test_frontend_route_smoke.py -q
```

Expected: FAIL until the Vue page contains the new anchors.

### Task 2: Polish Admin AI Agent Page

**Files:**
- Modify: `frontend/src/views/admin/AIAgentConfig.vue`

- [x] **Step 1: Update page header and summary cards**

Replace the English eyebrow and raw introduction with Chinese governance copy. Add four summary cards: total agents, enabled agents, local contracts, and provider modes.

- [x] **Step 2: Add governance strip**

Add a compact three-column explanation row:

- `本地契约层`: workflow only speaks stable JSON contracts.
- `Provider适配`: GJT, mock, local model, and manual import normalize into the same shape.
- `教师采纳门槛`: AI output enters business data only after teacher review/adoption.

- [x] **Step 3: Improve provider display**

Show provider status tags for `Mock开发模式`, `桂教通预留`, `本地模型预留`, and `人工导入`.

- [x] **Step 4: Improve contract panel**

Rename the side panel to `本地契约层`, show provider modes, adoption rule, and thinking progress descriptions.

- [x] **Step 5: Improve detail drawer**

Add sections for `Provider配置`, `调用契约`, `思考进度`, and `采纳规则`, while keeping existing JSON contract previews.

- [x] **Step 6: Improve create/edit dialog guidance**

Make GJT fields clearly reserved configuration. Add copy explaining secrets must stay in environment variables or backend provider settings, not browser-visible JSON.

### Task 3: Verify, Smoke, Commit, Push

**Files:**
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
- Modify: `docs/superpowers/plans/2026-05-26-ai-agent-page-polish.md`

- [x] **Step 1: Run targeted tests**

Run:

```powershell
python -m pytest backend/tests/test_ai_agent_page_polish.py backend/tests/test_frontend_route_smoke.py backend/tests/test_frontend_text_health.py -q
```

Expected: all tests pass.

- [x] **Step 2: Run full release check**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check-release.ps1
```

Expected: backend tests, compile, text health, route smoke, and frontend build pass.

- [x] **Step 3: Browser smoke**

Open `http://127.0.0.1:3000/admin/ai-agents` and verify the page visibly contains:

- `AI智能体治理`
- `本地契约层`
- `Provider适配`
- `教师采纳门槛`
- `桂教通预留`

- [x] **Step 4: Commit and push**

Run:

```powershell
git diff --check
git status --short
git add backend/tests/test_ai_agent_page_polish.py scripts/check_frontend_route_smoke.py frontend/src/views/admin/AIAgentConfig.vue docs/superpowers/plans/2026-05-26-ai-agent-page-polish.md docs/superpowers/progress/2026-05-25-platform-progress.md
git commit -m "Polish AI agent management page"
git push origin codex/agent-contract-crud
```
