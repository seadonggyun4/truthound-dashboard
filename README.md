# truthound-dashboard

Truthound Dashboard is the operational UI for Truthound 3.0. It keeps the
existing dashboard visual language and Intlayer-based application i18n while
resetting the product surface to the APIs and namespaces that actually exist in
Truthound 3.0.

## What ships in 3.0

- Source management and schema learning
- Validation runs, rule management, validation history, and detailed run views
- Profiling, profile comparison, and rule suggestion workflows
- Drift comparison via `truthound.drift.compare`
- Privacy workflows via `truthound.scan` and `truthound.mask`
- Lineage, anomaly, reports, Data Docs, plugins, storage, observability
- Checkpoint-oriented schedules, notifications, alerts, throttling, escalation,
  and trigger monitoring

Removed from the 3.0 dashboard surface:

- Glossary, catalog, activity/collaboration
- Dashboard-only maintenance product surfaces
- Drift monitor, schema watcher, and standalone model monitoring products
- Mock/demo execution paths and legacy phase-based compatibility messaging

## Requirements

- Python 3.11+
- Node.js 20+
- `truthound>=3.0.0`

## Installation

```bash
pip install truthound-dashboard
```

For local development:

```bash
pip install -e ".[dev,docs]"
cd frontend
npm install
```

## Usage

```bash
truthound serve
truthound serve --port 9000
truthound serve --reload
```

The dashboard is available at `http://localhost:8765` by default.

## Documentation

The canonical docs source lives in [`docs/`](./docs) in this repository and is
also mirrored into the main Truthound documentation site under the
`dashboard/` section.

Local docs build:

```bash
mkdocs build --strict
```

## Verification

Recommended local checks:

```bash
python -m pytest
cd frontend && npm run type-check
cd frontend && npm run build
mkdocs build --strict
```
