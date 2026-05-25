# User Account Portability Design

## Goal

Add trial-operation account initialization for teachers and students so a school can import real users after organization base data is ready.

## Scope

This phase adds JSON package template, export, dry-run import, and committed import for user accounts. It does not import historical submissions, evaluations, projects, or guardian accounts.

## API Contract

- `GET /api/v1/users/data/template`
  - System administrators only.
  - Returns a sample user package.
- `GET /api/v1/users/data/export`
  - System administrators only.
  - Exports active users without password hashes or initial passwords.
- `POST /api/v1/users/data/import`
  - System administrators only.
  - Accepts `{ "dry_run": true, "package": { "users": [...] } }`.
  - `dry_run=true` validates and reports counts without writing.
  - `dry_run=false` creates only missing usernames.

## Package Format

```json
{
  "users": [
    {
      "username": "qz-teacher-001",
      "name": "张老师",
      "role": "teacher",
      "school_code": "qz01",
      "class": null,
      "initial_password": "password"
    },
    {
      "username": "qz-student-001",
      "name": "学生一",
      "role": "student",
      "school_code": "qz01",
      "class": {
        "grade": "七年级",
        "name": "七年级(1)班",
        "academic_year": "2025-2026"
      },
      "initial_password": "password"
    }
  ]
}
```

## Rules

- Usernames are the dedupe key.
- Existing usernames are skipped and never overwritten.
- `initial_password` is required for new users and must be at least six characters.
- Student rows must include a class object that resolves within the referenced school.
- Non-student roles may include no class.
- The import result returns initial passwords only for newly created users in the current request.
- Export never returns passwords.
- Import is additive and non-destructive.

## Data Flow

1. Administrator downloads the template or prepares JSON from school roster data.
2. Administrator pastes the JSON into the user management import dialog.
3. Dry-run validates schools, classes, roles, passwords, and duplicate usernames.
4. Formal import creates missing users with hashed initial passwords.
5. The UI shows created, skipped, errors, and the temporary account handout list.

## Error Handling

Validation errors are collected per row where possible. Rows with missing school, missing class, unsupported role, weak password, or duplicate username inside the same package are not created. Existing usernames are skipped instead of treated as errors.

## Testing

Backend tests cover template, export password redaction, dry-run no-write behavior, committed import, student class binding, repeated import skips, login with generated password, and non-admin blocking. Frontend build verifies the admin page compiles after adding import/export controls.
