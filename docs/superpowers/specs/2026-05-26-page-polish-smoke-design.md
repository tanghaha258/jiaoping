# Phase 9 Page Polish And Smoke Design

## Goal

Turn the current operational platform into a more reliable demo and trial surface by making visible page quality measurable. Phase 9 focuses on navigation/page text health, critical role routes, and repeatable smoke checks before broader page-by-page visual polish.

## Scope

This phase is intentionally narrow for the first batch:

- Verify router titles and global navigation labels are valid UTF-8 Chinese text.
- Detect replacement characters, mojibake fragments, and obvious broken template fragments in frontend source.
- Ensure critical role routes keep their expected titles and mounted view files.
- Add the text-health check to the release check so future changes cannot silently reintroduce garbled copy.
- Update the progress tracker with Phase 9 and Phase 10 as the next work tracks.

The page-by-page UI polish will build on this baseline in later Phase 9 batches.

## Current Findings

PowerShell `Get-Content` can display Chinese text as mojibake in this environment, but direct UTF-8 reads through Node show that route titles and many layout strings are correct. The actual risk is not every displayed terminal artifact; the risk is unverified source text and missing automated guardrails.

## Design

Add a lightweight Python static check at `scripts/check_frontend_text_health.py`. It reads selected frontend files with UTF-8, recursively extracts source text, and fails on:

- Unicode replacement character `U+FFFD`.
- Common mojibake tokens such as `鐧`, `鏁`, `瀛`, `璺`, `绠`, `璧`, `鎻`, `閽`, and similar fragments when they appear in UTF-8 source.
- Known broken Vue/template fragments such as `?/span>` or unterminated `aria-label` text.
- Missing expected route titles for core public, teacher, student, research, and admin routes.
- Missing expected global navigation labels in `AppLayout.vue` and `RoleMenu.vue`.

The check is static by design: it is fast, deterministic, and can run during release checks without starting a browser.

## Testing

Add `backend/tests/test_frontend_text_health.py` because existing repository-level artifact tests already live under backend pytest. The tests will:

- Assert the script exists and exits successfully.
- Assert the script reports `Frontend text health check passed.`.
- Assert release checks call the script.
- Assert critical source files contain expected labels when read as UTF-8.

This gives us a red-green loop before adding the script and release-check integration.

## Follow-up Batches

After this baseline lands, continue Phase 9 with browser smoke for admin, teacher, student, and research roles. Then polish pages in this order:

1. Admin: dashboard, AI agents, settings, users, schools.
2. Teacher: dashboard, AI lesson plan, projects, project detail, resource center, evaluations.
3. Student: task list, task detail, submission detail, profile.
4. Research: dashboard, templates, resource review.

## Phase 10 Direction

Phase 10 will build the AI local contract foundation below the visible pages. GJT is a competition integration provider, not the platform core. The platform core should expose stable scenario contracts, provider adapters, thinking/progress events, call records, structured output normalization, adoption gates, and provider-neutral error metadata. GJT, local model providers, and OpenAI-compatible providers should all plug into that contract without changing business workflows.
