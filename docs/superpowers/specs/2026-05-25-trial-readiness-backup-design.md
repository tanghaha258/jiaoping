# Trial Readiness and Backup Design

## Goal

Give trial operators a concrete readiness checklist and a repeatable local backup/restore path before the platform is used by a real school.

## Scope

This phase adds an admin-facing trial readiness API and dashboard panel, plus PowerShell scripts for SQLite backup and restore. It does not add cloud backup scheduling, object-storage sync, or database migration tooling.

## Readiness Contract

`GET /api/v1/dashboard/trial-readiness` returns:

```json
{
  "status": "ready",
  "checked_at": "2026-05-25T00:00:00Z",
  "summary": { "ok": 7, "warning": 1, "error": 0 },
  "items": [
    {
      "key": "organization_data",
      "label": "基础组织数据",
      "status": "ok",
      "description": "学校、班级、学科已初始化，可以支撑试运行。",
      "metric": "学校 1 / 班级 1 / 学科 7",
      "action": "在学校管理中导入基础数据",
      "route": "/admin/schools"
    }
  ]
}
```

Allowed item statuses are `ok`, `warning`, and `error`. Overall status is `ready` when no item is `error`; otherwise it is `action_required`.

## Checklist Items

- Service readiness: verifies database, upload directory, seed data, and AI provider mode.
- Organization data: active schools, classes, and subjects exist.
- User accounts: teacher and student accounts exist.
- AI contract: at least one enabled lesson-plan agent exists.
- Teaching workflow data: at least one active or completed project exists.
- Student task availability: at least one published or closed task exists.
- Resources: at least one active or published resource exists.
- Backup path: SQLite database file exists or non-SQLite backup instructions are shown.

Errors block trial readiness. Warnings are acceptable for optional-but-important trial items, such as missing published tasks or resources.

## Backup Scripts

- `scripts/backup-sqlite.ps1`
  - Finds the SQLite database from `backend/.env` or defaults to `backend/app.db`.
  - Copies it into `backups/` with a timestamped filename.
  - Supports `-DatabasePath` and `-BackupDir`.
- `scripts/restore-sqlite.ps1`
  - Restores a selected backup to the SQLite database path.
  - Requires `-BackupPath`.
  - Creates a pre-restore backup beside the target unless `-SkipSafetyBackup` is supplied.

## Frontend

The admin dashboard shows a compact checklist panel with status tags, metrics, and quick links to the relevant management pages. The panel should use the existing quiet admin dashboard style and should not become a landing page.

## Testing

Backend tests cover admin access, checklist shape, non-admin blocking, and script/docs artifacts. Frontend build verifies dashboard integration. A smoke test logs in as admin and confirms the checklist panel renders on `/admin`.
