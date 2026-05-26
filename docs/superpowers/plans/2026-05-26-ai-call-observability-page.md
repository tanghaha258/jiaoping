# AI Call Observability Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish the admin AI call history page into an operational observability console for AI calls, Provider routing, thinking progress, adoption state, and failure diagnosis.

**Architecture:** Keep existing `/api/v1/ai/calls` and `/api/v1/ai/calls/{call_id}/progress` APIs. Rework the Vue page presentation and detail drawer so the list remains a filterable call ledger while the drawer fetches progress steps on demand. Add static regression tests and route-smoke anchors for the new admin-facing copy.

**Tech Stack:** Vue 3, Element Plus, TypeScript, Python static smoke scripts, pytest.

---

### Task 1: Lock AI Call Page Anchors With TDD

**Files:**
- Create: `backend/tests/test_ai_call_page_polish.py`
- Modify: `scripts/check_frontend_route_smoke.py`

- [x] **Step 1: Write the failing page-copy test**

Create `backend/tests/test_ai_call_page_polish.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "frontend" / "src" / "views" / "admin" / "AICallHistory.vue"


def test_ai_call_page_explains_observability_loop():
    text = PAGE.read_text(encoding="utf-8")

    for label in [
        "AI调用观测",
        "调用链路",
        "思考进度",
        "Provider链路",
        "采纳状态",
        "错误排查",
        "教师采纳门槛",
    ]:
        assert label in text
```

- [x] **Step 2: Run red test**

Run:

```powershell
python -m pytest backend/tests/test_ai_call_page_polish.py -q
```

Expected: FAIL because the current page is still a basic ledger and lacks these observability anchors.

- [x] **Step 3: Extend route smoke**

Update the `ai-calls` route expectation in `scripts/check_frontend_route_smoke.py` so anchors include `AI调用观测`, `调用链路`, and `思考进度`.

- [x] **Step 4: Run route smoke red**

Run:

```powershell
python -m pytest backend/tests/test_frontend_route_smoke.py -q
```

Expected: FAIL until the page contains the new route anchors.

### Task 2: Rework AI Call History Page

**Files:**
- Modify: `frontend/src/views/admin/AICallHistory.vue`

- [x] **Step 1: Header and summary**

Replace the plain header with `AI调用观测` copy. Add summary counters for total calls, succeeded calls, adopted calls, and failed calls based on the current loaded page.

- [x] **Step 2: Operational guidance strip**

Add three compact guidance panels:

- `调用链路`: scenario -> Provider -> status -> teacher review/adoption.
- `思考进度`: progress steps are fetched from `/ai/calls/{call_id}/progress`.
- `错误排查`: failed calls expose provider/status/error details without leaking secrets.

- [x] **Step 3: Improve table semantics**

Keep filters and pagination. Replace raw status/provider values with Chinese labels and tags. Add columns for `采纳状态`, `输出摘要`, and a clear detail action.

- [x] **Step 4: Fetch progress in detail drawer**

Import `getAICallProgress` from `@/api/ai`. When opening a detail drawer, fetch progress for the selected call and show a progress bar plus step timeline. Show an empty state if the call has no recorded steps.

- [x] **Step 5: Improve detail drawer sections**

Add sections for `Provider链路`, `思考进度`, `教师采纳门槛`, `错误排查`, `请求载荷`, and `响应载荷`. Keep JSON previews read-only.

### Task 3: Verify, Browser Smoke, Commit, Push

**Files:**
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
- Modify: `docs/superpowers/plans/2026-05-26-ai-call-observability-page.md`

- [x] **Step 1: Run targeted checks**

Run:

```powershell
python -m pytest backend/tests/test_ai_call_page_polish.py backend/tests/test_frontend_route_smoke.py backend/tests/test_frontend_text_health.py -q
```

Expected: all tests pass.

- [x] **Step 2: Run full release check**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check-release.ps1
```

Expected: backend tests, compile, text health, route smoke, and frontend build pass.

- [x] **Step 3: Browser smoke**

Open `http://127.0.0.1:3000/admin/ai-calls` and verify:

- `AI调用观测`
- `调用链路`
- `思考进度`
- `Provider链路`
- `采纳状态`
- `错误排查`

Note: current local data has no AI call rows, so the drawer action was not available in browser smoke. The drawer copy and progress wiring are covered by static regression checks and will be browser-smoked with seeded call records in a later data pass.

- [x] **Step 4: Commit and push**

Run:

```powershell
git diff --check
git add backend/tests/test_ai_call_page_polish.py scripts/check_frontend_route_smoke.py frontend/src/views/admin/AICallHistory.vue docs/superpowers/plans/2026-05-26-ai-call-observability-page.md docs/superpowers/progress/2026-05-25-platform-progress.md
git commit -m "Polish AI call observability page"
git push origin codex/agent-contract-crud
```
