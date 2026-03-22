# Artifacts

## Purpose and permissions

These endpoints define the canonical generated-output surface of the dashboard. Reports
and Data Docs both use `/artifacts`. There is no canonical `/reports/*` REST family.

## Canonical endpoints

- `GET /artifacts/capabilities`
- `GET /artifacts`
- `GET /artifacts/statistics`
- `GET /artifacts/{artifact_id}`
- `GET /artifacts/{artifact_id}/download`
- `DELETE /artifacts/{artifact_id}`
- `POST /artifacts/cleanup`
- `POST /artifacts/validations/{validation_id}/report`
- `POST /artifacts/validations/{validation_id}/datadocs`

## Query/filter contract

Artifact listing supports `workspace_id`, `saved_view_id`, `source_id`, `validation_id`,
`artifact_type`, `format`, `status`, `include_expired`, `search`, `offset`, and
`limit`. Artifact saved views are limited to the `artifacts` scope.

## Request body shape

Report generation accepts format, theme, locale, title, sample controls, statistics
controls, and custom metadata. Data Docs generation accepts theme and title. Delete and
cleanup operations require artifact write access.

## Response shape

Artifact responses include workspace, source, validation, artifact type, format,
status, title, metadata, download statistics, freshness data, `external_url`, and
`download_url`. Capabilities responses include supported formats, themes, locales, and
artifact types.

## Example request/response

```http
POST /api/v1/artifacts/validations/val_123/report
```

```json
{
  "format": "html",
  "theme": "professional",
  "locale": "en"
}
```

## UI screens that consume the API

- `/reports` browser route
- Validation detail artifact actions
- Dashboard overview artifact slices

## Common errors

- `404` when the validation or artifact does not exist in the current workspace
- `403` when the role lacks artifact write access
- `404` on download when the stored file or external URL is no longer valid
