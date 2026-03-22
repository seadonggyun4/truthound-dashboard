# API Reference Overview and Conventions

## Purpose and permissions

This section documents the canonical REST contracts exposed by Truthound Dashboard. The
API follows the same product boundary as the UI: control-plane behavior lives here, but
Truthound core remains the source of truth for validation semantics.

## Canonical endpoints

The most important families are:

- `/auth/session`, `/me`, `/workspaces`, `/roles`, `/permissions`, `/users`, `/views`,
  and `/overview`
- `/sources`
- `/validations`
- `/artifacts`
- `/alerts` and `/incident-queues`
- `/notifications`

## Query/filter contract

Control-plane list APIs standardize on `workspace_id`, `saved_view_id`, `search`,
`status`, `offset`, and `limit` when the concept applies. Ownership-aware surfaces add
`owner_user_id`, `team_id`, and `domain_id`. Incident-aware surfaces add `queue_id`
and `assignee_user_id`.

## Request body shape

Request bodies are JSON and use dashboard-native schemas that align with the Truthound
3.0 control-plane model. Secret-bearing fields may be supplied during create or rotate
operations but are never returned in full on read paths.

## Response shape

List responses typically include `data` or `items`, `total`, `offset`, and `limit`.
Single-resource responses return the resource directly. Artifact responses include
download URLs and typed artifact metadata. Session responses include user, workspace,
role, and effective permissions.

## Example request/response

Request:

```http
GET /api/v1/artifacts?artifact_type=report&status=ready&limit=20
```

Response:

```json
{
  "data": [],
  "total": 0,
  "offset": 0,
  "limit": 20
}
```

## UI screens that consume the API

- Session bootstrap and shell header
- Sources
- History
- Alerts
- `/reports` artifact index
- Notifications and queue configuration

## Common errors

- `401` when the session is missing or invalid
- `403` when the role lacks the required permission
- `404` when the workspace-scoped resource does not exist
- `422` for invalid request payloads
