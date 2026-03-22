# Auth and Control Plane

## Purpose and permissions

These endpoints manage session bootstrap, workspace context, permissions, users, teams,
domains, saved views, and overview data. Read and write access is permission-gated by
workspace.

## Canonical endpoints

- `GET /auth/session`
- `POST /auth/session`
- `DELETE /auth/session`
- `GET /me`
- `GET /workspaces`
- `GET /roles`
- `GET /permissions`
- `GET /users`
- `GET /teams`, `POST /teams`
- `GET /domains`, `POST /domains`
- `GET /views`, `POST /views`, `PUT /views/{view_id}`, `DELETE /views/{view_id}`
- `GET /overview`

## Query/filter contract

Saved views are filtered by `scope`. Overview is workspace-scoped through the active
session or an explicit workspace context where supported.

## Request body shape

Session creation accepts a password and optional workspace identifier. Team and domain
creation accept names, slugs, and descriptions. Saved view writes accept a scope,
filters payload, default flag, and descriptive metadata.

## Response shape

Session responses include token, expiry, user, workspace, and role. Saved view
responses include owner, workspace, scope, filters, and timestamps. Overview responses
include source, incident, and artifact slices plus queue backlog, assignee workload,
ownership counts, and saved views.

## Example request/response

```http
GET /api/v1/views?scope=alerts
```

```json
{
  "data": [],
  "total": 0,
  "offset": 0,
  "limit": 100
}
```

## UI screens that consume the API

- Sign-in flow
- Shell header
- Overview
- Sources ownership selectors
- Saved view bars

## Common errors

- `401` for invalid session bootstrap
- `403` for permission-restricted administrative routes
- `404` for unknown workspace-scoped objects
