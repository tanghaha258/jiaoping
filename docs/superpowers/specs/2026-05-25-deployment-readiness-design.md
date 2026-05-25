# Deployment Readiness Design

## Goal

Make the current AI-agent-driven teaching-assessment platform deployable for a school trial without changing the business workflow. The trial operator should be able to configure the app, start it locally or with Docker, check whether it is ready, and run a repeatable smoke test.

## Scope

- Add operational health signals:
  - Liveness: the API process is reachable.
  - Readiness: database connectivity, upload directory access, core seed data, and AI provider mode are visible.
- Add deployment configuration examples that preserve the existing local-contract-first AI provider model.
- Add scripts for local start, release checks, and smoke checks.
- Add deployment documentation that explains local trial and Docker trial paths.

## Non-Goals

- Do not replace the current app architecture.
- Do not implement the real Guangxi JiaoTong API call before final API documents arrive.
- Do not publish AI-generated content directly to students.
- Do not introduce a new frontend API base pattern in this phase; the frontend continues using `/api/v1` behind Vite or Nginx proxy.

## Runtime Contract

### Health Endpoints

- `GET /api/v1/health`
  - No authentication.
  - Confirms the API process is alive.
  - Returns `status`, `service`, `version`, and `environment`.
- `GET /api/v1/health/ready`
  - No authentication.
  - Confirms the deployment can serve the operational loop.
  - Returns:
    - `status`: `ready` or `degraded`.
    - `checks.database.status`
    - `checks.uploads.status`
    - `checks.seed_data.status`
    - `ai_provider.mode`
    - `ai_provider.gjt_configured`

### Configuration

Backend `.env` keeps these first-phase deployment knobs:

- `APP_NAME`
- `APP_ENV`
- `DEBUG`
- `DATABASE_URL`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `UPLOAD_DIR`
- `MAX_UPLOAD_MB`
- `GJT_API_BASE_URL`
- `GJT_API_KEY`
- `GJT_AGENT_ID`
- `GJT_API_TIMEOUT_SECONDS`
- `CORS_ORIGINS`

Frontend `.env` stays intentionally small:

- `VITE_APP_TITLE`
- `VITE_API_PROXY_TARGET`

`VITE_API_PROXY_TARGET` documents the local dev proxy target but does not change the runtime API path.

## Acceptance Criteria

- Backend tests prove liveness/readiness endpoints return structured readiness data.
- Repository tests prove deployment docs, env examples, and smoke script exist with required keys.
- Smoke script can check a running API and optionally login to exercise the AI contract endpoint.
- Deployment docs give repeatable Windows local trial and Docker trial commands.
- Progress tracker records Phase 4 completion.
