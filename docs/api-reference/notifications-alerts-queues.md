# Notifications, Alerts, and Queues

## Purpose and permissions

These endpoints manage notification channels, notification rules, queue configuration,
and the alert or incident workbench. Read and write scopes are separated because many
operators need to triage incidents without changing delivery configuration.

## Canonical endpoints

- `GET /notifications/channels/types`
- `GET /notifications/channels`
- `POST /notifications/channels`
- `GET /notifications/channels/{channel_id}`
- `PUT /notifications/channels/{channel_id}`
- `POST /notifications/channels/{channel_id}/credentials/rotate`
- `POST /notifications/channels/{channel_id}/test`
- `GET /notifications/rules`
- `POST /notifications/rules`
- `GET /alerts`
- `GET /alerts/{alert_id}`
- `POST /alerts/{alert_id}/assign`
- `POST /alerts/{alert_id}/acknowledge`
- `POST /alerts/{alert_id}/resolve`
- `GET /incident-queues`
- `PUT /incident-queues/{queue_id}/members`

## Query/filter contract

Alerts support `workspace_id`, `saved_view_id`, `source`, `severity`, `status`,
`queue_id`, `assignee_user_id`, `search`, `offset`, and `limit`. Notification channel
lists support pagination and channel-type filtering.

## Request body shape

Notification channel writes accept channel metadata plus type-specific config.
Secret-bearing fields may be provided on create, update, or rotate but are returned
only as redacted config on read. Alert actions accept messages and assignment targets.

## Response shape

Channel responses include redacted config, `config_version`, `has_stored_secrets`, and
`credential_updated_at`. Alert responses include queue and assignee identity plus
timeline-ready state. Queue responses include membership metadata.

## Example request/response

```http
GET /api/v1/alerts?queue_id=queue_123&status=open
```

```json
{
  "items": [],
  "total": 0,
  "offset": 0,
  "limit": 50
}
```

## UI screens that consume the API

- Notifications
- Notifications Advanced
- Alerts

## Common errors

- `403` when operators lack incident or notification write permissions
- `404` when a queue, alert, or channel is not visible in the current workspace
- `422` when channel config is invalid or a rotate payload is incomplete
