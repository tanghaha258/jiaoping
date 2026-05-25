# Organization Data Portability Design

## Goal

Make trial setup less dependent on manual CRUD by adding an organization data package contract. Operators can export current base data, download a template, dry-run an import, and commit an import after checking the summary.

## Scope

- Export active `regions`, `schools`, `classes`, and `subjects` as structured JSON.
- Provide a JSON template with one valid sample chain.
- Import by codes/names:
  - Regions by `code`.
  - Schools by `code`, linked to a region `code`.
  - Classes by `school_code`, `grade`, `name`, and `academic_year`.
  - Subjects by `name`.
- Support `dry_run` so operators can validate counts before writing data.
- Restrict import/export/template endpoints to `system_admin`.

## Non-Goals

- No Excel parsing in this phase.
- No destructive synchronization or deletion.
- No user account import in this phase.

## API Contract

- `GET /api/v1/org/data/template`
- `GET /api/v1/org/data/export`
- `POST /api/v1/org/data/import`

Import request:

```json
{
  "dry_run": true,
  "package": {
    "regions": [{ "name": "钦州试点区", "code": "qz-trial" }],
    "schools": [{ "region_code": "qz-trial", "name": "试点学校", "code": "trial-school", "status": "active" }],
    "classes": [{ "school_code": "trial-school", "grade": "七年级", "name": "七年级(1)班", "academic_year": "2026-2027" }],
    "subjects": [{ "name": "地理", "stage": "junior_high" }]
  }
}
```

Response summary:

```json
{
  "dry_run": true,
  "created": { "regions": 1, "schools": 1, "classes": 1, "subjects": 1 },
  "skipped": { "regions": 0, "schools": 0, "classes": 0, "subjects": 0 },
  "errors": []
}
```

## Acceptance Criteria

- Dry-run import returns expected counts and does not create records.
- Commit import creates records and links schools/classes correctly.
- Re-importing the same package skips existing records.
- Non-admin users cannot export/import organization packages.
- Frontend has visible import/export/template controls on school management.
