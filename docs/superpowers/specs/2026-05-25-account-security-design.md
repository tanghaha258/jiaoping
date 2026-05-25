# Account Security Design

## Goal

Remove the biggest trial-operation account risk: default seeded passwords must be replaceable through real UI and APIs before the platform is handed to a school.

## Scope

- Authenticated users can change their own password after entering the current password.
- System admins can reset another user's password from user management.
- Password changes write audit logs.
- Frontend exposes:
  - Teacher settings password form.
  - Admin user-management reset password dialog.

## Non-Goals

- No SMS/email verification in this phase.
- No forced password rotation policy in this phase.
- No session blacklist; existing JWTs remain valid until expiry, which matches current token architecture.

## API Contract

### `POST /api/v1/auth/change-password`

Request:

```json
{
  "current_password": "old-password",
  "new_password": "new-password"
}
```

Rules:

- Requires an authenticated active user.
- `new_password` length: 6-100.
- Current password must match.
- New password must differ from current password.

### `POST /api/v1/users/{user_id}/reset-password`

Request:

```json
{
  "new_password": "new-password"
}
```

Rules:

- Requires `system_admin`.
- Target user must exist.
- `new_password` length: 6-100.

## Acceptance Criteria

- After a user changes password, login with the old password fails and login with the new password succeeds.
- A wrong current password blocks self-service change.
- Non-admin users cannot reset another user's password.
- Admin reset makes the old target password invalid and the new password valid.
- Frontend build passes with real API calls wired.
