# Plugins, Lineage, Anomaly, and Observability

## Purpose and permissions

This page groups the active platform-oriented APIs that do not fit cleanly into source,
artifact, or incident families but are still part of the supported dashboard surface.

## Canonical endpoints

- Plugin inventory and lifecycle endpoints under `/plugins`
- Lineage endpoints under `/lineage`
- Anomaly endpoints under `/anomaly`
- Observability endpoints under `/observability`
- Storage tiering endpoints under `/tiers`, `/policies`, `/configs`, `/migrations`

## Query/filter contract

These families vary by surface. Plugins focus on search and lifecycle transitions.
Observability focuses on status and settings. Storage tiering uses resource-specific
filters rather than a single shared model.

## Request body shape

Plugin requests manage install or enable transitions. Lineage requests create or update
graph-related records. Anomaly requests run or retrieve model-backed comparisons.
Observability settings writes update runtime behavior for metrics or status reporting.

## Response shape

Responses are resource-specific but all remain workspace- or deployment-scoped and free
of removed legacy products such as standalone model monitoring or custom plugin
authoring.

## Example request/response

```http
GET /api/v1/plugins
```

```json
{
  "items": []
}
```

## UI screens that consume the API

- Plugins
- Lineage
- Anomaly and ML pages
- Observability
- Storage tiering

## Common errors

- `404` for unknown plugin or lineage objects
- `403` for restricted platform mutations
- `422` for invalid lifecycle or anomaly payloads
