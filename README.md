# truthound-dashboard

> **Alpha Version**: APIs and features may change without notice.

## Overview
<img width="300" height="300" alt="Truthound_icon" src="https://github.com/user-attachments/assets/90d9e806-8895-45ec-97dc-f8300da4d997" />

[![PyPI version](https://img.shields.io/pypi/v/truthound-dashboard.svg)](https://pypi.org/project/truthound-dashboard/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](https://opensource.org/licenses/Apache-2.0)
[![Powered by Intlayer](https://img.shields.io/badge/Powered%20by-Intlayer-yellow.svg)](https://intlayer.org)
[![Downloads](https://img.shields.io/pepy/dt/truthound-dashboard?color=brightgreen)](https://pepy.tech/project/truthound-dashboard)

A web-based data quality monitoring dashboard for [truthound](https://github.com/seadonggyun4/truthound).

truthound-dashboard provides a graphical interface for managing data sources, executing validations, tracking historical results, scheduling automated checks, and configuring notifications. It serves as an alternative to commercial data quality platforms.

[Documentation](https://truthound.netlify.app) | [PyPI](https://pypi.org/project/truthound-dashboard/) | [Live Demo](https://truthound-dashboard.vercel.app)

> **Demo Note**: The live demo uses a free-tier backend ([Render](https://render.com)), which enters sleep mode after 15 minutes of inactivity. The first request may take 30–60 seconds to wake up the server.

## Design Principles

- **Zero-Config**: Works out of the box with sensible defaults
- **Single Process**: No Redis, Celery, or PostgreSQL required
- **Local First**: Full functionality without cloud dependencies
- **GX Cloud Parity**: Match paid features for free

## Feature Comparison with GX Cloud

| Feature | GX Cloud (Paid) | truthound-dashboard |
|---------|-----------------|---------------------|
| Data Source Management | Available | Available |
| Schema Learning | Available | Available |
| Validation Execution | Available | Available (289+ validators) |
| Validation History | Available | Available |
| Scheduled Validations | Available | Available (6 trigger types) |
| Notifications | Available | Available (9 channels) |
| Drift Detection | Available | Available (14 methods) |
| Data Profiling | Available | Available |
| PII Scan & Masking | Available | Available (GDPR/CCPA/LGPD) |
| Anomaly Detection | Limited | Available (6 ML algorithms) |
| Data Lineage | Available | Available (4 renderers) |
| Model Monitoring | Available | Available |
| Reports & Export | Available | Available (6 formats) |
| Plugin Marketplace | Not Available | Available |
| Storage Tiering | Not Available | Available |
| Dark Mode & i18n | Limited | Available (2 languages + AI translation) |
| License | Commercial | Apache 2.0 |

## Requirements

- Python 3.11 or higher
- truthound >= 1.2.10

## Installation

```bash
pip install truthound-dashboard
```

This command automatically installs [truthound](https://github.com/seadonggyun4/truthound) as a dependency.

## Usage

```bash
# Start the dashboard server (default port: 8765)
truthound serve

# Specify a custom port
truthound serve --port 9000

# Enable development mode with hot reload
truthound serve --reload

# Disable automatic browser opening
truthound serve --no-browser
```

The dashboard interface is accessible at `http://localhost:8765`.

## Features

### Data Management

| Feature | Description | Documentation |
|---------|-------------|---------------|
| **Dashboard** | Overview statistics and quick navigation | [docs/data-management/dashboard.md](./docs/data-management/dashboard.md) |
| **Data Sources** | CSV, Parquet, JSON, 13 database connectors (PostgreSQL, MySQL, SQLite, BigQuery, Snowflake, etc.) | [docs/data-management/sources.md](./docs/data-management/sources.md) |
| **Data Catalog** | Asset metadata, column-level management, quality scores, sensitivity classification | [docs/data-management/catalog.md](./docs/data-management/catalog.md) |
| **Business Glossary** | Term definitions, categories, relationships, lifecycle management | [docs/data-management/glossary.md](./docs/data-management/glossary.md) |

### Data Quality

| Feature | Description | Documentation |
|---------|-------------|---------------|
| **Validations** | 289+ validators across 15 categories, per-validator configuration, severity override, parallel execution | [docs/data-quality/validations.md](./docs/data-quality/validations.md) |
| **Drift Detection** | 14 statistical methods (KS, PSI, Chi2, JS, Wasserstein, etc.), column-level comparison | [docs/data-quality/drift.md](./docs/data-quality/drift.md) |
| **Drift Monitoring** | Continuous monitoring with alerts, root cause analysis, remediation suggestions | [docs/data-quality/drift-monitoring.md](./docs/data-quality/drift-monitoring.md) |
| **Schema Evolution** | Change tracking, breaking/warning/safe classification, version timeline | [docs/data-quality/schema-evolution.md](./docs/data-quality/schema-evolution.md) |
| **Schema Watcher** | Real-time schema change detection, rename detection, alert thresholds | [docs/data-quality/schema-watcher.md](./docs/data-quality/schema-watcher.md) |
| **Profile Comparison** | Longitudinal profile analysis, delta computation, trend charts | [docs/data-quality/profile-comparison.md](./docs/data-quality/profile-comparison.md) |
| **Privacy & PII** | PII detection (`th.scan`), data masking (`th.mask`), GDPR/CCPA/LGPD compliance | [docs/data-quality/privacy.md](./docs/data-quality/privacy.md) |
| **Data Lineage** | Interactive graph visualization (D3/Mermaid/Cytoscape), impact analysis, OpenLineage integration | [docs/data-quality/lineage.md](./docs/data-quality/lineage.md) |
| **Quality Reporter** | Quality scoring with F1/Precision/Recall metrics, multi-format export | [docs/data-quality/quality-reporter.md](./docs/data-quality/quality-reporter.md) |
| **Enterprise Sampling** | Block, multi-stage, column-aware, progressive strategies for 100M+ rows | [docs/data-quality/enterprise-sampling.md](./docs/data-quality/enterprise-sampling.md) |
| **Rule Suggestions** | AI-powered rule generation from data profiles, confidence scoring | [docs/data-quality/rule-suggestions.md](./docs/data-quality/rule-suggestions.md) |

### ML & Monitoring

| Feature | Description | Documentation |
|---------|-------------|---------------|
| **Anomaly Detection** | 6 ML algorithms (IsolationForest, Z-Score, IQR, MAD, Ensemble, DistributionDrift), streaming support | [docs/ml-monitoring/anomaly.md](./docs/ml-monitoring/anomaly.md) |
| **Model Monitoring** | ML model performance tracking, metric monitoring, alert rules, model versioning | [docs/ml-monitoring/model-monitoring.md](./docs/ml-monitoring/model-monitoring.md) |

### System

| Feature | Description | Documentation |
|---------|-------------|---------------|
| **Unified Alerts** | Cross-feature alert aggregation, severity filtering, correlation and grouping | [docs/system/alerts.md](./docs/system/alerts.md) |
| **Schedules** | 6 trigger types (cron, interval, data change, composite, event, manual), validator configuration | [docs/system/schedules.md](./docs/system/schedules.md) |
| **Trigger Monitoring** | Real-time trigger health, cooldown tracking, webhook management, execution history | [docs/system/trigger-monitoring.md](./docs/system/trigger-monitoring.md) |
| **Activity Feed** | System event timeline, collaboration comments, change tracking | [docs/system/activity.md](./docs/system/activity.md) |
| **Notifications** | 9 channels (Slack, Email, Webhook, Discord, Telegram, PagerDuty, OpsGenie, Teams, GitHub) | [docs/system/notifications.md](./docs/system/notifications.md) |
| **Advanced Notifications** | Rule-based routing, deduplication (4 strategies), throttling (5 methods), multi-level escalation | [docs/system/notifications-advanced.md](./docs/system/notifications-advanced.md) |
| **Reports** | 6 formats (HTML, PDF, CSV, JSON, Excel, Markdown), statistics dashboard, lifecycle management | [docs/system/reports.md](./docs/system/reports.md) |
| **Plugins** | Marketplace, 4 plugin types, custom validator/reporter creation, security levels | [docs/system/plugins.md](./docs/system/plugins.md) |
| **Storage Tiering** | Hot/Warm/Cold/Archive tiers, 6 policy types, composite AND/OR logic, migration history | [docs/system/storage-tiering.md](./docs/system/storage-tiering.md) |
| **Observability** | Audit logging, metrics collection, distributed tracing | [docs/system/observability.md](./docs/system/observability.md) |
| **Maintenance** | Retention policies, auto-cleanup, database optimization (VACUUM), cache management | [docs/system/maintenance.md](./docs/system/maintenance.md) |

## Internationalization

truthound-dashboard implements internationalization using [Intlayer](https://intlayer.org), a modern i18n framework that provides type-safe translations with component-level content declaration.

### Built-in Languages

The dashboard ships with **2 fully translated languages**:
- **English (en)** - Complete UI translation
- **Korean (ko)** - Complete UI translation

These languages are immediately available without additional configuration or setup.

### Extending Language Support

The dashboard can be extended to support 15+ additional languages using the AI-powered `translate` command. This CLI tool translates all UI content files from the built-in English and Korean to your target language.

**Note:** Additional languages are not included in the default installation and must be generated using the translation CLI before deployment.

#### Supported AI Providers

| Provider | Environment Variable | Models |
|----------|---------------------|--------|
| OpenAI | `OPENAI_API_KEY` | GPT-4o, GPT-4o-mini, GPT-4, GPT-3.5 |
| Anthropic | `ANTHROPIC_API_KEY` | Claude Sonnet 4, Claude Opus 4 |
| Mistral | `MISTRAL_API_KEY` | Mistral Large, Mistral Small |
| Ollama | Not required | Llama 3.2, Mistral, Qwen (local execution) |

#### Configuration

API credentials are configured through environment variables. This approach ensures that sensitive credentials are not exposed in command history or application logs.

**Temporary Session Configuration**

```bash
# OpenAI
export OPENAI_API_KEY=sk-xxxxxxxxxxxx
truthound translate -l fr -p openai

# Anthropic
export ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx
truthound translate -l fr -p anthropic

# Mistral
export MISTRAL_API_KEY=xxxxxxxxxxxx
truthound translate -l fr -p mistral
```

**Persistent Configuration**

```bash
# Add to shell configuration file (~/.bashrc or ~/.zshrc)
echo 'export OPENAI_API_KEY=sk-xxxxxxxxxxxx' >> ~/.zshrc
source ~/.zshrc
```

**Inline Configuration**

```bash
OPENAI_API_KEY=sk-xxx truthound translate -l fr -p openai
```

#### Usage Examples

```bash
# Translate to French using OpenAI
truthound translate -l fr -p openai

# Translate to multiple languages
truthound translate -l ja,zh,de,fr -p anthropic

# Use local Ollama (no API key required)
truthound translate -l fr -p ollama

# Auto-detect available provider
truthound translate -l fr

# Preview files without making changes
truthound translate -l fr --dry-run

# List available providers and their status
truthound translate --list-providers

# List supported language codes
truthound translate --list-languages
```

#### Security Considerations

| Aspect | Risk Level | Description |
|--------|------------|-------------|
| Network transmission | None | API keys are used locally and transmitted only to the selected provider |
| Source code exposure | None | Credentials are injected via environment variables |
| Build artifact inclusion | None | Only translated content is persisted; credentials are not stored |
| API communication | Standard | Requests are made directly to provider endpoints using user credentials |

#### Supported Languages

The translation system supports 36 languages including: Arabic, Bulgarian, Chinese, Croatian, Czech, Danish, Dutch, English, Estonian, Finnish, French, German, Greek, Hebrew, Hindi, Hungarian, Indonesian, Italian, Japanese, Korean, Latvian, Lithuanian, Malay, Norwegian, Polish, Portuguese, Romanian, Russian, Slovak, Slovenian, Spanish, Swedish, Thai, Turkish, Ukrainian, and Vietnamese.

Execute `truthound translate --list-languages` to view the complete list with language codes.

## Technology Stack

**Backend**
- FastAPI
- SQLAlchemy 2.0 (async)
- SQLite with aiosqlite
- APScheduler
- Pydantic 2.x

**Frontend**
- React 18
- TypeScript
- Vite
- TailwindCSS
- shadcn/ui
- Zustand
- [Intlayer](https://intlayer.org) (internationalization)

## Documentation

Full documentation is available at [https://truthound.netlify.app](https://truthound.netlify.app).

- [Getting Started](./docs/getting-started.md)
- [Architecture](./docs/architecture.md)
- [All Documentation](./docs/index.md)

## Related Projects

- [truthound](https://github.com/seadonggyun4/truthound) - Core data validation library
- [truthound-orchestration](https://github.com/seadonggyun4/truthound-orchestration) - Pipeline orchestration integration

## License

This project is licensed under the Apache License 2.0.
