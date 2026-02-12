# Truthound Dashboard

> **Open-Source Data Quality Monitoring Platform** — A comprehensive alternative to GX Cloud

Truthound Dashboard is an open-source data quality monitoring platform that provides capabilities comparable to [GX Cloud](https://greatexpectations.io/gx-cloud/) at no cost. The system is designed to democratize enterprise-grade data quality tooling by delivering a full-featured monitoring solution under the Apache 2.0 license.

## Comparative Analysis

| Feature | GX Cloud | Truthound Dashboard |
|---------|----------|---------------------|
| UI-based Rule Editing | Paid | **Free** |
| Validation History | Paid | **Free** |
| Scheduled Validations | Paid | **Free** |
| Slack/Email Notifications | Paid | **Free** |
| Auto Schema Generation | Paid | **Free** |
| Drift Detection | Paid | **Free** |
| Unlimited Users | Team Plan | **Free** |
| **Pricing** | **Subscription** | **$0** |

## Quick Start

```bash
# Installation
pip install truthound-dashboard

# Launch (browser opens automatically)
truthound serve
```

The dashboard becomes operational within seconds of invocation.

## Key Capabilities

### Data Sources
Connect to CSV, Parquet, PostgreSQL, MySQL, Snowflake, BigQuery, and additional data sources through a unified connector framework.

### Visual Schema Editor
Create and modify validation schemas through the graphical interface without manual code authoring.

### Validation History
Track data quality trends over time through chronological validation records with statistical analysis.

### Scheduled Validations
Configure automated validation execution using cron-based scheduling with six distinct trigger types.

### Notifications
Receive alerts via Slack, Email, or Webhook (among nine supported channels) when validations fail.

### Auto Schema Generation
Automatically generate schemas from data characteristics using `th.learn` with configurable constraint inference.

### Drift Detection
Compare two datasets to detect schema and distribution changes using 14 statistical methods.

### Dark Mode and Internationalization
Full support for dark/light themes and multiple languages (English, Korean built-in, 15+ via AI translation).

### AI-Powered Translation
Translate the UI to any supported language using OpenAI, Anthropic, Ollama, or Mistral with a single CLI command.

## Documentation

### Getting Started
- [Getting Started](./getting-started.md) — Installation and initial configuration guide
- [Architecture](./architecture.md) — System design and component specifications
- [Internationalization Guide](./intlayer-i18n-Guide.md) — i18n framework and AI translation guide

### Data Management
- [Dashboard](./data-management/dashboard.md) — Aggregate statistics and navigation overview
- [Data Sources](./data-management/sources.md) — Source connection and lifecycle management
- [Data Catalog](./data-management/catalog.md) — Asset metadata and governance repository
- [Business Glossary](./data-management/glossary.md) — Business terminology standardization

### Data Quality
- [Validations](./data-quality/validations.md) — Validation execution, history, versioning, and custom rules; includes Truthound core engine integration (PHASE 1–5: Result Format, Structured Results, DAG Execution, Exception Isolation)
- [Drift Detection](./data-quality/drift.md) — Statistical distribution comparison
- [Drift Monitoring](./data-quality/drift-monitoring.md) — Continuous drift surveillance
- [Schema Evolution](./data-quality/schema-evolution.md) — Structural change tracking and version history
- [Schema Watcher](./data-quality/schema-watcher.md) — Continuous schema monitoring with rename detection
- [Profile Comparison](./data-quality/profile-comparison.md) — Longitudinal profile analysis and trend identification
- [Privacy and PII](./data-quality/privacy.md) — PII detection and masking
- [Data Lineage](./data-quality/lineage.md) — Data flow visualization and impact analysis
- [Quality Reporter](./data-quality/quality-reporter.md) — Quality scoring and multi-format reporting
- [Enterprise Sampling](./data-quality/enterprise-sampling.md) — Large-scale sampling for 100M+ row datasets
- [Rule Suggestions](./data-quality/rule-suggestions.md) — AI-powered validation rule generation

### ML and Monitoring
- [Anomaly Detection](./ml-monitoring/anomaly.md) — ML-based outlier detection
- [Model Monitoring](./ml-monitoring/model-monitoring.md) — ML model performance tracking

### System
- [Unified Alerts](./system/alerts.md) — Centralized alert management and correlation
- [Schedules](./system/schedules.md) — Automated validation scheduling
- [Trigger Monitoring](./system/trigger-monitoring.md) — Trigger health, cooldown tracking, and webhook management
- [Activity Feed](./system/activity.md) — System event timeline and collaboration
- [Notifications](./system/notifications.md) — Multi-channel alert delivery
- [Advanced Notifications](./system/notifications-advanced.md) — Routing, deduplication, throttling, escalation
- [Reports](./system/reports.md) — Multi-format report generation
- [Plugins](./system/plugins.md) — Extensibility framework and custom extensions
- [Storage Tiering](./system/storage-tiering.md) — Data lifecycle management with composite policies
- [Observability](./system/observability.md) — Audit logging, metrics, and distributed tracing
- [Maintenance](./system/maintenance.md) — System maintenance and database optimization

## Live Demo

Experience the dashboard at:

**[https://truthound-dashboard.netlify.app](https://truthound-dashboard.netlify.app)**

> The demo operates in mock mode using MSW (Mock Service Worker) without a backend connection.
> For actual data validation operations, install the package locally.

## Truthound Core Engine Integration

Truthound Dashboard maintains a systematic bidirectional integration with the Truthound core validation engine (v1.3.0). The core engine underwent a five-phase enhancement programme, each of which necessitated corresponding adaptations in the dashboard's backend adapter, result converter, Pydantic schemas, and frontend TypeScript types:

| Phase | Enhancement | Dashboard Impact |
|-------|-------------|-----------------|
| **PHASE 1** | Result Format System | `result_format` parameter propagation (4-level progressive disclosure) |
| **PHASE 2** | Structured Results | `ValidationDetail`, `ReportStatistics` schema extensions |
| **PHASE 3** | Metric Deduplication | No dashboard changes (internal optimisation; improved response latency) |
| **PHASE 4** | DAG Execution | `ValidatorExecutionSummary` with skip/dependency tracking |
| **PHASE 5** | Exception Isolation | `catch_exceptions`/`max_retries` parameters; `ExceptionInfo`/`ExceptionSummary` schemas |

For detailed integration specifications, refer to the [Architecture](./architecture.md) and [Validations](./data-quality/validations.md) documentation.

## Links

- [GitHub Repository](https://github.com/seadonggyun4/truthound-dashboard)
- [PyPI Package](https://pypi.org/project/truthound-dashboard/)
- [truthound Core Library](https://github.com/seadonggyun4/truthound)

## License

Apache License 2.0
