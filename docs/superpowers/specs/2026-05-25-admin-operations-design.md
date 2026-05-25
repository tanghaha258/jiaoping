# Admin Operations Phase 3 Design

## Goal

Make the deployment administrator experience operational: admins can maintain users, schools, classes, subjects, system settings, audit logs, and AI call records without editing seed data or database rows manually.

## Scope

This phase focuses on the admin console after the teaching loop is usable:

- User management uses real create, update, status, and detail APIs.
- School management handles regions, schools, classes, and subjects as layered data.
- System settings can be listed and edited as JSON values.
- Audit logs and AI call history become readable ledgers with filters and detail drawers.
- Existing API response contracts and role checks stay consistent with the rest of the platform.

Bulk import, password reset workflows, complex role delegation, and production-grade RBAC policy editing remain out of scope for this phase.

## Backend Design

Add an `org` router for operational base data:

- `GET/POST/PATCH/DELETE /api/v1/org/regions`
- `GET/POST/PATCH/DELETE /api/v1/org/schools`
- `GET/POST/PATCH/DELETE /api/v1/org/classes`
- `GET/POST/PATCH/DELETE /api/v1/org/subjects`

Deletes are soft deletes where the model supports `deleted_at`; subjects and regions can be deactivated by deletion semantics in the service response even if the table has no status column. School admins are scoped to their school for class operations. System admins can manage all records.

Add a `settings` router:

- `GET /api/v1/settings`
- `PUT /api/v1/settings/{key}`

Settings values remain JSON so provider, deployment, and feature flags can be stored without schema churn. The frontend validates JSON before sending it.

User APIs keep their current endpoints but the frontend no longer treats them as placeholders. User creation validates username uniqueness, creates active accounts, and class/school choices come from org APIs.

## Frontend Design

Admin pages use the same layered pattern:

- Header band with a short operational title and refresh/create controls.
- Filterable table for the main list.
- Detail drawer for read-only inspection.
- Create/edit dialog for mutations.
- Explicit empty states instead of demo data.

`SchoolManagement.vue` uses tabs:

- Schools
- Classes
- Subjects
- Regions

This avoids cramming four entity types into one flat table while still keeping basic data management in one admin module.

`UserManagement.vue` includes role, school, class, and status filters. Editing a user does not expose password reset in this phase. Creating a user requires username, name, role, password, optional school, and optional class.

`SystemSettings.vue` lists key/value settings and edits the JSON value in a dialog. Invalid JSON blocks submission client-side.

`AuditLogViewer.vue` and `AICallHistory.vue` are ledgers with filters and detail drawers. They do not mutate records.

## Data Rules

- System admins can manage all org data and users.
- School admins can inspect scoped data but broad destructive actions remain system-admin only.
- Student and teacher users must not access admin base-data APIs.
- System settings are edited as JSON objects, arrays, strings, numbers, booleans, or null.
- AI call and audit ledgers should expose request/detail JSON safely in read-only preformatted blocks.

## Verification

- Backend pytest covers org CRUD, setting upsert, user create/update/status, and role blocking.
- Frontend production build must pass.
- Browser smoke covers admin login, user page, school page tabs, settings page, audit page, and AI call page rendering against real APIs.
