# Reports and Data Docs

Reporting surfaces are aligned to:

- `truthound.reporters`
- `truthound.datadocs`

The dashboard now uses a single operational artifact model for both generated
reports and Data Docs.

## Canonical storage

- Reports and Data Docs are persisted as `artifact_records`
- `artifact_type` starts with `report` and `datadocs`
- `/artifacts` is the canonical REST surface for browsing, generation,
  download, cleanup, and overview rollups
- the browser route `/reports` remains the artifact index UI entry point, but
  all REST contracts resolve through `/artifacts`

## Operational workflow

1. Run or inspect a validation backed by Truthound 3.0
2. Generate a report or Data Docs artifact from the validation
3. Browse the artifact index in `/reports`
4. Download the file or open Data Docs directly from the artifact record
5. Treat reports and Data Docs as the same artifact lifecycle with different
   `artifact_type` values

## What the dashboard does not do

- It does not invent a second reporting engine
- It does not maintain dashboard-only scoring semantics
- It does not keep a separate Data Docs runtime outside Truthound
