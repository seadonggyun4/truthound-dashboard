# truthound-dashboard
<img width="1697" height="847" alt="truthound-dashboard" src="https://github.com/user-attachments/assets/2239ebff-470b-49fe-ab09-81bc3117880d" />

> **Alpha Version**: APIs and features may change without notice.

## Overview
<img width="300" height="300" alt="Truthound_icon" src="https://github.com/user-attachments/assets/90d9e806-8895-45ec-97dc-f8300da4d997" />

[![PyPI version](https://img.shields.io/pypi/v/truthound-dashboard.svg)](https://pypi.org/project/truthound-dashboard/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](https://opensource.org/licenses/Apache-2.0)
[![Powered by Intlayer](https://img.shields.io/badge/Powered%20by-Intlayer-yellow.svg)](https://intlayer.org)
[![Downloads](https://img.shields.io/pepy/dt/truthound-dashboard?color=brightgreen)](https://pepy.tech/project/truthound-dashboard)

Truthound Dashboard is a web-based data quality monitoring platform for the [truthound](https://github.com/seadonggyun4/truthound) validation library. It provides a graphical interface for managing data sources, executing validations, tracking historical results, scheduling automated checks, and configuring notifications. The system is designed as an open-source alternative to commercial data quality platforms, offering equivalent or superior functionality under the Apache 2.0 license.

[Documentation](https://truthound.netlify.app) | [PyPI](https://pypi.org/project/truthound-dashboard/) | [Live Demo](https://truthound-dashboard.vercel.app)

> **Demo Note**: The live demo operates on a free-tier backend ([Render](https://render.com)), which enters a dormant state after 15 minutes of inactivity. Initial requests may require 30–60 seconds for server initialization.

## Architectural Design Principles

- **Zero-Configuration**: Operational immediately upon installation with sensible defaults
- **Single-Process Architecture**: No external dependencies on Redis, Celery, or PostgreSQL
- **Local-First Design**: Complete functionality without cloud service dependencies
- **GX Cloud Feature Parity**: Equivalent or superior capabilities to commercial alternatives

## Comparative Analysis with GX Cloud

| Feature | GX Cloud (Commercial) | Truthound Dashboard |
|---------|----------------------|---------------------|
| Data Source Management | Available | Available |
| Schema Learning | Available | Available |
| Validation Execution | Available | Available (289+ validators) |
| Validation History | Available | Available |
| Scheduled Validations | Available | Available (6 trigger types) |
| Notifications | Available | Available (9 channels) |
| Drift Detection | Available | Available (14 statistical methods) |
| Data Profiling | Available | Available |
| PII Scan and Masking | Available | Available (GDPR/CCPA/LGPD) |
| Anomaly Detection | Limited | Available (6 ML algorithms) |
| Data Lineage | Available | Available (4 renderers) |
| Model Monitoring | Available | Available |
| Reports and Export | Available | Available (6 formats) |
| Progressive Result Detail | Not Available | Available (4 levels: BOOLEAN_ONLY → COMPLETE) |
| Exception Isolation and Auto-Retry | Not Available | Available (3-tier fallback, circuit breaker) |
| DAG-Based Validator Scheduling | Not Available | Available (dependency-driven conditional execution) |
| Plugin Marketplace | Not Available | Available |
| Storage Tiering | Not Available | Available |
| Dark Mode and i18n | Limited | Available (2 languages + AI translation) |
| License | Commercial | Apache 2.0 |

## Truthound Core Engine Integration

Truthound Dashboard maintains a systematic bidirectional integration with the Truthound core validation engine (v1.3.0), which has undergone a five-phase enhancement programme. Each phase introduced capabilities that are fully propagated through the dashboard's backend adapter, result converter, Pydantic schemas, and frontend TypeScript type declarations.

| Phase | Enhancement | Dashboard Integration |
|-------|-------------|----------------------|
| **PHASE 1** | Result Format System | Four-level progressive disclosure (`BOOLEAN_ONLY`, `BASIC`, `SUMMARY`, `COMPLETE`) controlling validation output granularity |
| **PHASE 2** | Structured Results | `ValidationDetail` per-issue metrics, `ReportStatistics` aggregate analytics, multi-dimensional issue breakdowns |
| **PHASE 3** | Metric Deduplication | Transparent internal optimisation; improved validation response latency without API surface changes |
| **PHASE 4** | DAG Execution | Dependency-based conditional validator scheduling; execution summary with skip/dependency tracking |
| **PHASE 5** | Exception Isolation | Fault-tolerant execution with 3-tier fallback, auto-retry with exponential backoff, circuit breaker, and exception classification |

All integration changes adhere to a strict backward compatibility protocol: new fields are declared as `Optional` with `None` defaults, Pydantic schemas apply `ConfigDict(extra="ignore")`, and the converter employs defensive `getattr()` patterns throughout.

## System Requirements

- Python 3.11 or higher
- truthound >= 1.2.10

## Installation

```bash
pip install truthound-dashboard
```

This command automatically installs [truthound](https://github.com/seadonggyun4/truthound) as a transitive dependency.

## Usage

```bash
# Launch the dashboard server (default port: 8765)
truthound serve

# Specify a custom port
truthound serve --port 9000

# Enable development mode with hot module replacement
truthound serve --reload

# Suppress automatic browser invocation
truthound serve --no-browser
```

The dashboard interface is accessible at `http://localhost:8765`.

## Feature Taxonomy

### Data Management

| Feature | Description | Documentation |
|---------|-------------|---------------|
| **Dashboard** | Aggregate statistics and navigation overview | [docs/data-management/dashboard.md](./docs/data-management/dashboard.md) |
| **Data Sources** | CSV, Parquet, JSON, 13 database connectors (PostgreSQL, MySQL, SQLite, BigQuery, Snowflake, etc.) | [docs/data-management/sources.md](./docs/data-management/sources.md) |
| **Data Catalog** | Asset metadata repository with column-level management, quality scoring, and sensitivity classification | [docs/data-management/catalog.md](./docs/data-management/catalog.md) |
| **Business Glossary** | Standardized terminology definitions, hierarchical categories, semantic relationships, and lifecycle governance | [docs/data-management/glossary.md](./docs/data-management/glossary.md) |

### Data Quality

| Feature | Description | Documentation |
|---------|-------------|---------------|
| **Validations** | 289+ validators across 15 categories with per-validator configuration, severity override, parallel execution, 4-level progressive result format (PHASE 1), structured result analytics (PHASE 2), DAG-based conditional execution (PHASE 4), and fault-tolerant exception isolation with auto-retry (PHASE 5) | [docs/data-quality/validations.md](./docs/data-quality/validations.md) |
| **Drift Detection** | 14 statistical methods (KS, PSI, Chi2, JS, Wasserstein, etc.) with column-level comparison | [docs/data-quality/drift.md](./docs/data-quality/drift.md) |
| **Drift Monitoring** | Continuous monitoring with alerting, root cause analysis, and remediation guidance | [docs/data-quality/drift-monitoring.md](./docs/data-quality/drift-monitoring.md) |
| **Schema Evolution** | Structural change tracking with breaking/warning/safe classification and version timeline | [docs/data-quality/schema-evolution.md](./docs/data-quality/schema-evolution.md) |
| **Schema Watcher** | Real-time schema monitoring with similarity-based rename detection and alert thresholds | [docs/data-quality/schema-watcher.md](./docs/data-quality/schema-watcher.md) |
| **Profile Comparison** | Longitudinal profile analysis with delta computation and trend visualization | [docs/data-quality/profile-comparison.md](./docs/data-quality/profile-comparison.md) |
| **Privacy and PII** | PII detection (`th.scan`), data masking (`th.mask`), GDPR/CCPA/LGPD compliance support | [docs/data-quality/privacy.md](./docs/data-quality/privacy.md) |
| **Data Lineage** | Interactive graph visualization (D3/Mermaid/Cytoscape) with impact analysis and OpenLineage integration | [docs/data-quality/lineage.md](./docs/data-quality/lineage.md) |
| **Quality Reporter** | Confusion matrix-based quality scoring (F1/Precision/Recall) with multi-format export | [docs/data-quality/quality-reporter.md](./docs/data-quality/quality-reporter.md) |
| **Enterprise Sampling** | Block, multi-stage, column-aware, and progressive strategies for datasets exceeding 100M rows | [docs/data-quality/enterprise-sampling.md](./docs/data-quality/enterprise-sampling.md) |
| **Rule Suggestions** | Profile-driven automated rule generation with confidence scoring | [docs/data-quality/rule-suggestions.md](./docs/data-quality/rule-suggestions.md) |

### ML and Monitoring

| Feature | Description | Documentation |
|---------|-------------|---------------|
| **Anomaly Detection** | 6 ML algorithms (IsolationForest, Z-Score, IQR, MAD, Ensemble, DistributionDrift) with streaming support | [docs/ml-monitoring/anomaly.md](./docs/ml-monitoring/anomaly.md) |
| **Model Monitoring** | ML model performance tracking with metric monitoring, alert rules, and model versioning | [docs/ml-monitoring/model-monitoring.md](./docs/ml-monitoring/model-monitoring.md) |

### System

| Feature | Description | Documentation |
|---------|-------------|---------------|
| **Unified Alerts** | Cross-feature alert aggregation with severity filtering, correlation, and grouping | [docs/system/alerts.md](./docs/system/alerts.md) |
| **Schedules** | 6 trigger types (cron, interval, data change, composite, event, manual) with validator configuration | [docs/system/schedules.md](./docs/system/schedules.md) |
| **Trigger Monitoring** | Real-time trigger health surveillance, cooldown tracking, webhook management, and execution history | [docs/system/trigger-monitoring.md](./docs/system/trigger-monitoring.md) |
| **Activity Feed** | System event timeline with collaboration comments and change tracking | [docs/system/activity.md](./docs/system/activity.md) |
| **Notifications** | 9 channels (Slack, Email, Webhook, Discord, Telegram, PagerDuty, OpsGenie, Teams, GitHub) | [docs/system/notifications.md](./docs/system/notifications.md) |
| **Advanced Notifications** | Rule-based routing, deduplication (4 strategies), throttling (5 methods), multi-level escalation | [docs/system/notifications-advanced.md](./docs/system/notifications-advanced.md) |
| **Reports** | 6 formats (HTML, PDF, CSV, JSON, Excel, Markdown) with statistics dashboard and lifecycle management | [docs/system/reports.md](./docs/system/reports.md) |
| **Plugins** | Marketplace with 4 plugin types, custom validator/reporter creation, and security levels | [docs/system/plugins.md](./docs/system/plugins.md) |
| **Storage Tiering** | Hot/Warm/Cold/Archive tiers with 6 policy types, composite AND/OR logic, and migration history | [docs/system/storage-tiering.md](./docs/system/storage-tiering.md) |
| **Observability** | Audit logging, metrics collection, and distributed tracing | [docs/system/observability.md](./docs/system/observability.md) |
| **Maintenance** | Retention policies, automated cleanup, database optimization (VACUUM), and cache management | [docs/system/maintenance.md](./docs/system/maintenance.md) |

## Internationalization

Truthound Dashboard implements internationalization using [Intlayer](https://intlayer.org), a modern framework that provides type-safe translations with component-level content declaration and compile-time validation.

### Built-in Languages

The dashboard ships with **2 fully translated languages**:
- **English (en)** — Complete UI translation
- **Korean (ko)** — Complete UI translation

These languages are immediately available without additional configuration.

### Extending Language Support

The dashboard can be extended to support 15+ additional languages using the AI-powered `translate` command. This CLI tool translates all UI content files from the built-in languages to the specified targets.

> **Note:** Additional languages are not included in the default installation and must be generated using the translation CLI prior to deployment.

#### Supported AI Providers

| Provider | Environment Variable | Models |
|----------|---------------------|--------|
| OpenAI | `OPENAI_API_KEY` | GPT-4o, GPT-4o-mini, GPT-4, GPT-3.5 |
| Anthropic | `ANTHROPIC_API_KEY` | Claude Sonnet 4, Claude Opus 4 |
| Mistral | `MISTRAL_API_KEY` | Mistral Large, Mistral Small |
| Ollama | Not required | Llama 3.2, Mistral, Qwen (local execution) |

#### Configuration

API credentials are configured through environment variables, ensuring that sensitive credentials are not exposed in command history or application logs.

```bash
export OPENAI_API_KEY=sk-xxxxxxxxxxxx
truthound translate -l fr -p openai
```

#### Usage Examples

```bash
# Translate to multiple languages simultaneously
truthound translate -l ja,zh,de,fr -p anthropic

# Local execution via Ollama (no API key required)
truthound translate -l fr -p ollama

# Auto-detect available provider
truthound translate -l fr

# Preview without file modifications
truthound translate -l fr --dry-run
```

#### Security Considerations

| Aspect | Risk Level | Description |
|--------|------------|-------------|
| Network transmission | None | API keys are used locally and transmitted only to the selected provider |
| Source code exposure | None | Credentials are injected via environment variables |
| Build artifact inclusion | None | Only translated content is persisted; credentials are not stored |

#### Supported Languages

The translation system supports 36 languages. Execute `truthound translate --list-languages` to view the complete list with ISO 639-1 language codes.

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

- [Getting Started](./docs/getting-started.md) — Installation and initial validation workflow
- [Architecture](./docs/architecture.md) — System design, component specifications, and core engine integration architecture
- [Validations](./docs/data-quality/validations.md) — Validation execution framework with PHASE 1–5 integration specifications
- [All Documentation](./docs/index.md) — Comprehensive documentation index

## Related Projects

- [truthound](https://github.com/seadonggyun4/truthound) — Core data validation library
- [truthound-orchestration](https://github.com/seadonggyun4/truthound-orchestration) — Pipeline orchestration integration

## License

This project is licensed under the Apache License 2.0.
