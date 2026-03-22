# Validations, Profiles, and History

## Purpose and permissions

These endpoints cover validation execution and retrieval, profile generation and
comparison, rule suggestions, and source-specific validation history. They require read
or write access to the corresponding source and workflow.

## Canonical endpoints

- `POST /validations/sources/{source_id}/validate`
- `GET /validations/{validation_id}`
- `GET /validations/sources/{source_id}/validations`
- `POST /profile/sources/{source_id}`
- `POST /profile/comparisons`
- `GET /profile/{profile_id}`
- `GET /sources/{source_id}/history`
- `POST /rule-suggestions`

## Query/filter contract

Validation list endpoints are source-scoped. History accepts `period` and
`granularity`. Saved views apply to the `history` scope on the UI side rather than as a
global validations list scope.

## Request body shape

Validation run requests include validator selection, schema options, result detail
controls, and execution controls. Profile and comparison requests identify sources or
profile baselines to compare.

## Response shape

Validation detail returns canonical run fields plus issue and execution issue detail.
Validation list responses return source-scoped summaries. History returns summary,
trend, failure-frequency, and recent validation slices.

## Example request/response

```http
GET /api/v1/sources/src_123/history?period=30d&granularity=daily
```

```json
{
  "summary": {
    "total_runs": 0,
    "passed_runs": 0,
    "failed_runs": 0,
    "success_rate": 0
  },
  "trend": [],
  "failure_frequency": [],
  "recent_validations": []
}
```

## UI screens that consume the API

- Source detail validation panel
- Validation detail view
- Profile and comparison screens
- Source history page

## Common errors

- `404` when the source or validation is missing
- `422` when validator or profile payloads are malformed
- `500` when a comparison or history aggregation fails downstream
