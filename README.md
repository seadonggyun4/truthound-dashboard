# truthound-dashboard

[![PyPI version](https://img.shields.io/pypi/v/truthound-dashboard.svg)](https://pypi.org/project/truthound-dashboard/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](https://opensource.org/licenses/Apache-2.0)
[![Powered by Intlayer](https://img.shields.io/badge/Powered%20by-Intlayer-yellow.svg)](https://intlayer.org)
[![Downloads](https://img.shields.io/pepy/dt/truthound-dashboard?color=brightgreen)](https://pepy.tech/project/truthound-dashboard)

Truthound Dashboard is the operational UI for Truthound 3.0. It keeps the
existing dashboard visual language and Intlayer-based application i18n while
resetting the product surface to the APIs and namespaces that actually exist in
Truthound 3.0.

[Documentation](https://truthound.netlify.app/dashboard/) | [PyPI](https://pypi.org/project/truthound-dashboard/)

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

## Docs Entry Points

- Dashboard docs site: [https://truthound.netlify.app/dashboard/](https://truthound.netlify.app/dashboard/)
- Local docs source: [`docs/`](./docs)
- Main Truthound docs portal: [https://truthound.netlify.app/](https://truthound.netlify.app/)

Recommended reading order:

1. Quickstart
2. Concepts
3. Guides
4. API Reference

## Application I18n with Intlayer

Truthound Dashboard keeps its application-level internationalization on
[Intlayer](https://intlayer.org). The existing dashboard shell, page content,
labels, and component dictionaries remain Intlayer-based in the 3.0 reset.

- Built-in locales are currently `en` and `ko`.
- Frontend locale configuration lives in [`frontend/intlayer.config.mjs`](./frontend/intlayer.config.mjs).
- UI content dictionaries live alongside the frontend in `frontend/src/**/*.content.ts`.
- Additional locales can still be generated with the dashboard translation CLI.

Examples:

```bash
truthound translate -l ja,zh,de -p openai
truthound translate -l fr --dry-run
truthound translate --list-languages
```

The translation command updates Intlayer content files and the frontend locale
configuration without changing the dashboard's visual design system.

## Verification

Recommended local checks:

```bash
python -m pytest
cd frontend && npm run type-check
cd frontend && npm run build
mkdocs build --strict
```
