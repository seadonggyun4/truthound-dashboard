# Drift and Privacy

## Purpose and permissions

These endpoints expose drift comparisons, privacy scans, and masking workflows. They
support operators who need to compare states or process sensitive data without adding
dashboard-native engines.

## Canonical endpoints

- `POST /drift/compare`
- `GET /drift/{comparison_id}`
- `POST /scans`
- `GET /scans/{scan_id}`
- `POST /masks`
- `GET /masks/{mask_id}`

## Query/filter contract

Drift, scan, and mask requests are typically scoped by source, profile, or execution
identifier rather than broad list filtering.

## Request body shape

Drift requests identify the current and baseline states to compare. Privacy scan and
mask requests identify the source, scope, and any masking strategy or output options.

## Response shape

Responses include comparison or operation status, detailed findings, and identifiers for
later retrieval or triage.

## Example request/response

```http
POST /api/v1/drift/compare
```

```json
{
  "comparison_id": "cmp_123",
  "status": "completed"
}
```

## UI screens that consume the API

- Drift comparison screens
- Privacy scan views
- Masking result views

## Common errors

- `404` when the requested source or comparison target is missing
- `422` when the request omits required comparison or masking parameters
- `500` when downstream execution cannot materialize the requested input
