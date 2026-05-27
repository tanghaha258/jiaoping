# P10 Batch 3 AI Call Failure Observability Design

## Goal

Close Phase 10 with an operational failure-diagnosis loop for provider-neutral AI calls. The platform should persist safe, structured failure metadata, summarize failures for administrators, and connect AI Provider risks to trial readiness before real 桂教通 or other domestic providers are enabled.

## Current State

- AI calls are stored in `ai_agent_calls`.
- Failed calls currently preserve a human-readable `error_message`.
- Provider `metadata` can be attached to the immediate response, but it is not persisted as a stable call-ledger field.
- `/admin/ai-calls` already has an observability page and detail drawer, but failure diagnosis is mostly plain text.
- Provider readiness exists at `GET /api/v1/ai/agents/{agent_id}/readiness`.
- Admin trial readiness checks whether at least one enabled `lesson_plan` agent exists, but it does not yet inspect provider readiness or recent provider failures.

## Scope

This batch implements the complete operational loop:

1. Structured failure metadata for AI calls.
2. Provider failure classification.
3. Failure metadata persistence and API serialization.
4. AI call diagnostics aggregation.
5. `/admin/ai-calls` filtering and diagnostic UI.
6. Admin Dashboard / trial readiness risk item for AI Provider readiness and recent failures.

This batch does not integrate a live 桂教通 production API, add background retry workers, or add email/SMS alerts.

## Failure Metadata Contract

Each failed AI call should expose a safe metadata object:

```json
{
  "error_code": "configuration_missing",
  "error_category": "configuration_missing",
  "provider": "qwen_agent",
  "scenario": "lesson_plan",
  "retryable": false,
  "remediation": "补齐 Provider endpoint、model 和 api_key_env 后重新发起调用。",
  "upstream_status": null,
  "safe_metadata": {
    "model": "qwen-plus",
    "missing": ["endpoint", "api_key"]
  }
}
```

The metadata must never include API keys, bearer tokens, raw authorization headers, or complete upstream request bodies.

## Failure Categories

Use a small stable set of categories:

- `configuration_missing`: endpoint, model, api key, agent id, or other required local configuration is missing.
- `provider_unsupported`: the configured provider is not registered in the gateway.
- `upstream_unreachable`: DNS, refused connection, or network-level provider failure.
- `upstream_timeout`: provider call timed out.
- `upstream_bad_response`: provider response is not JSON or misses required response fields.
- `contract_validation_failed`: provider returned JSON, but the content does not satisfy the local scenario output contract.
- `unknown_error`: uncategorized provider or platform failure.

## Backend Design

### Data Persistence

Add a JSON column on `AIAgentCall` for structured metadata, using the existing SQLite-friendly JSON pattern:

- `diagnostic_metadata`: stores the safe failure metadata object for failed calls.

Keep `error_message` as the readable summary for backward compatibility and list display.

### Provider Result Metadata

Extend provider results so failure paths can return safe metadata. Existing provider success metadata remains usable, but failed calls should persist a normalized diagnostic object.

The OpenAI-compatible provider should classify:

- missing endpoint/model/key as `configuration_missing`;
- timeout as `upstream_timeout`;
- connection/URL errors as `upstream_unreachable`;
- JSON shape/content errors as `upstream_bad_response`.

Gateway-level unsupported provider errors should become `provider_unsupported`.

Unexpected exceptions in `AIService.initiate_call` should become `unknown_error`.

### Contract Validation

For `lesson_plan`, after provider success but before the call is considered successful, validate the normalized output contains the required top-level fields:

- `project`
- `tasks`
- `rubric`
- `resources`
- `teacher_notes`

If validation fails, mark the call as `failed` with category `contract_validation_failed`. This protects teacher workflows from accepting incomplete provider output.

### Diagnostics Summary API

Add an admin-readable diagnostics endpoint:

`GET /api/v1/ai/calls/diagnostics/summary`

Response shape:

```json
{
  "total_failed": 3,
  "by_category": [
    {"category": "configuration_missing", "count": 2},
    {"category": "upstream_bad_response", "count": 1}
  ],
  "by_provider": [
    {"provider": "qwen_agent", "count": 2},
    {"provider": "gjt_api", "count": 1}
  ],
  "recent_failures": [
    {
      "id": "call-id",
      "provider": "qwen_agent",
      "scenario": "lesson_plan",
      "error_category": "configuration_missing",
      "error_message": "Provider configuration is incomplete",
      "created_at": "2026-05-28T10:00:00Z"
    }
  ]
}
```

The endpoint should respect school isolation through the current user, matching existing call-list behavior.

### Filtering

Extend `GET /api/v1/ai/calls` with `error_category`. If present, filter failed calls whose diagnostic metadata has that category. SQLite JSON filtering can use SQLAlchemy JSON access where available, or a scoped post-filter after applying existing school/status/provider filters if compatibility is simpler for this codebase.

## Frontend Design

### API Types

Extend `AICallItem` with:

- `diagnostic_metadata`
- `error_category`

Add `getAICallDiagnosticsSummary`.

### AI Call Observability Page

Enhance `/admin/ai-calls`:

- Add summary cards for total failures, top failure category, affected providers, and recent provider failures.
- Add an error-category filter.
- Add a failure category column/tag.
- Replace the plain error alert in the drawer with an operations-diagnosis panel:
  - failure category;
  - retryable status;
  - remediation;
  - upstream status;
  - safe metadata preview.

Keep the page dense and operational. Avoid explanatory marketing copy; labels should support scanning and repeated admin use.

### Dashboard / Trial Readiness

Enhance the existing readiness checklist item for AI contract/provider readiness:

- `error`: no enabled `lesson_plan` agent.
- `error`: at least one enabled real provider agent is missing required local configuration.
- `warning`: recent real-provider AI calls failed.
- `ok`: lesson-plan agent exists and provider readiness does not show blockers.

The readiness item should link to `/admin/ai-agents` when configuration is the problem and `/admin/ai-calls` when recent runtime failures are the problem.

## Testing Strategy

Use TDD for implementation:

1. Backend tests for failure metadata creation and secret redaction.
2. Backend tests for OpenAI-compatible failure classification.
3. Backend tests for diagnostics summary and `error_category` filtering.
4. Backend tests for trial readiness AI Provider risk states.
5. Frontend static tests for AI call page diagnostic anchors and API type usage.
6. Release verification through `scripts/check-release.ps1`.

Browser smoke should open `/admin/ai-calls` and `/admin` after implementation if local services are available.

## Release Criteria

P10 Batch 3 is complete when:

- Failed AI calls persist structured, safe diagnostic metadata.
- The call list/detail APIs expose the metadata.
- `/admin/ai-calls` lets admins filter and inspect failure categories.
- Diagnostics summary data is visible on the AI call page.
- Trial readiness reflects AI Provider configuration and recent runtime failure risk.
- All targeted tests and release checks pass.
- Progress docs are updated, changes are committed, and the branch is pushed.
