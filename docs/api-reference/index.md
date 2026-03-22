# API Reference

The dashboard REST API is a thin operational layer over Truthound 3.0.

## Core domains

- `/auth/session`
- `/me`
- `/workspaces`
- `/users`
- `/roles`
- `/permissions`
- `/teams`
- `/domains`
- `/views`
- `/overview`
- `/sources`
- `/validations`
- `/schemas`
- `/profile`
- `/history`
- `/drift`
- `/scans`
- `/mask`
- `/schedules`
- `/notifications`
- `/alerts`
- `/incident-queues`
- `/artifacts`
- `/artifacts/capabilities`
- `/triggers`
- `/plugins`
- `/lineage`
- `/anomaly`
- `/observability`

## Contract rules

- validation responses normalize `ValidationRunResult`
- checkpoint-oriented views normalize `CheckpointResult.validation_run` and
  `validation_view`
- artifact browsing and generation normalize `artifact_records`
- source and notification-adjacent credentials are persisted as `secret_refs`
- notification channel detail is redacted by default and credential replacement
  uses `/notifications/channels/{id}/credentials/rotate`
- ownership selectors and overview slices normalize `teams`, `domains`, and
  `source_ownerships`
- canonical browse/list/detail/download flows live under `/artifacts`
- the browser route `/reports` is only a UI alias for the artifact index
- incident queue operations are workspace-aware and assignment-aware
- saved views are supported only for `sources`, `alerts`, `artifacts`, and
  `history`
- unsupported dashboard-only product domains are intentionally absent
