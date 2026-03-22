# Sources and Ownership

## Purpose and permissions

These endpoints manage source lifecycle, source testing, credential rotation, and
ownership assignments. They require source read or write permissions depending on the
action.

## Canonical endpoints

- `GET /sources`
- `POST /sources`
- `GET /sources/{source_id}`
- `PUT /sources/{source_id}`
- `DELETE /sources/{source_id}`
- `POST /sources/{source_id}/test`
- `POST /sources/{source_id}/credentials/rotate`
- `GET /sources/types`
- `GET /sources/{source_id}/ownership`
- `PUT /sources/{source_id}/ownership`

## Query/filter contract

List sources supports `saved_view_id`, `search`, `status`, `offset`, `limit`,
`owner_user_id`, `team_id`, and `domain_id`. The effective workspace comes from the
current session.

## Request body shape

Create and update requests include common source metadata and type-specific config.
Secret-bearing config is accepted on writes and stored through `secret_refs`. Ownership
updates carry the owner user, team, and domain identifiers that should be attached to
the source.

## Response shape

Source responses include basic metadata, environment, redacted config, timestamps, and
ownership fields. Ownership responses are scoped to the source and the current
workspace.

## Example request/response

```http
GET /api/v1/sources?team_id=team_123&status=active
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

- Sources list
- Source detail
- Source create and edit dialogs
- Ownership selectors

## Common errors

- `404` when the source does not exist in the current workspace
- `422` when the source type payload is invalid
- `403` when the role can read sources but cannot rotate credentials or mutate config
