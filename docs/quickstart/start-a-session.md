# Start a Session and Choose a Workspace

## What this page covers

This page explains how the dashboard creates a local session, how workspace context is
resolved, and what an operator should verify before performing any write action.

## Before you start

- The dashboard API is reachable.
- At least one workspace has been bootstrapped.
- You know which role and permission scope you expect to use during the session.

## UI path or entry point

Open the dashboard root page, then use the sign-in flow if a valid session does not
already exist. Workspace context is visible in the shell header and drives every
control-plane list or write action.

## Step-by-step workflow

1. Load the dashboard and allow it to request the current session through
   `GET /auth/session`.
2. If the request cannot restore a session, submit the password and optional
   workspace identifier through the sign-in form.
3. Verify the returned session payload. It should include the user, workspace, role,
   and effective permission list derived from normalized permission relations.
4. Open the workspace list if you need to confirm that the selected workspace matches
   the deployment slice you intend to operate.
5. Check the header context before creating sources, editing notifications, or
   acknowledging incidents. The dashboard always scopes control-plane actions to the
   active workspace.

## Expected outputs

- A session token with an expiry time.
- A concrete user, workspace, and role visible in the shell.
- Permission-aware navigation that hides or blocks routes you cannot operate.

## Failure modes and troubleshooting

- If the wrong workspace loads, end the session and create a new one with the desired
  workspace identifier.
- If your role is missing expected actions, inspect the permission matrix rather than
  searching for legacy inline role configuration.
- If a session silently expires, repeat the bootstrap flow and confirm the local
  session store or cookies are not being cleared.

## Related APIs

- `GET /auth/session`
- `POST /auth/session`
- `DELETE /auth/session`
- `GET /workspaces`
- `GET /me`

## Next steps

Continue to [Add Your First Source](add-your-first-source.md) after you confirm that
your workspace and permissions are correct.
