# Truthound Dashboard

> **Open-source Data Quality Dashboard** - A GX Cloud Alternative

Truthound Dashboard is an open-source data quality monitoring platform that provides features comparable to [GX Cloud](https://greatexpectations.io/gx-cloud/) at no cost.

## Feature Comparison

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

# Launch (opens browser automatically)
truthound serve
```

The dashboard will be accessible within seconds.

## Key Features

### Data Sources
Connect to CSV, Parquet, PostgreSQL, MySQL, Snowflake, BigQuery, and other data sources.

### Visual Schema Editor
Create and edit validation schemas through the UI without writing code.

### Validation History
Track data quality trends over time with historical validation records.

### Scheduled Validations
Configure automated validation runs using cron-based scheduling.

### Notifications
Receive alerts via Slack, Email, or Webhook when validations fail.

### Auto Schema Generation
Automatically generate schemas from your data using `th.learn`.

### Drift Detection
Compare two datasets to detect schema and distribution changes.

### Dark Mode & i18n
Support for dark/light themes and multiple languages (English, Korean).

### AI-Powered Translation
Translate the UI to any language using OpenAI, Anthropic, Ollama, or Mistral with a single command.

## Documentation

### Getting Started
- [Getting Started](./getting-started.md) - Installation and quick start guide
- [Architecture](./architecture.md) - System design and component overview
- [Internationalization Guide](./intlayer-i18n-Guide.md) - i18n and AI translation guide

### Data Management
- [Dashboard](./data-management/dashboard.md) - Overview and statistics
- [Data Sources](./data-management/sources.md) - Source connection and validation
- [Data Catalog](./data-management/catalog.md) - Asset metadata management
- [Business Glossary](./data-management/glossary.md) - Business terminology management

### Data Quality
- [Drift Detection](./data-quality/drift.md) - Distribution comparison
- [Drift Monitoring](./data-quality/drift-monitoring.md) - Continuous drift monitoring
- [Privacy & PII](./data-quality/privacy.md) - PII detection and masking
- [Data Lineage](./data-quality/lineage.md) - Data flow visualization

### ML & Monitoring
- [Anomaly Detection](./ml-monitoring/anomaly.md) - ML-based outlier detection
- [Model Monitoring](./ml-monitoring/model-monitoring.md) - ML model performance tracking

### System
- [Unified Alerts](./system/alerts.md) - Centralized alert management
- [Schedules](./system/schedules.md) - Automated validation scheduling
- [Activity Feed](./system/activity.md) - System event timeline
- [Notifications](./system/notifications.md) - Multi-channel alerting
- [Advanced Notifications](./system/notifications-advanced.md) - Routing, deduplication, escalation
- [Reports](./system/reports.md) - Multi-format report generation
- [Plugins](./system/plugins.md) - Extensibility and custom extensions
- [Maintenance](./system/maintenance.md) - System maintenance and cleanup

## Live Demo

Experience the dashboard at:

**[https://truthound-dashboard.netlify.app](https://truthound-dashboard.netlify.app)**

> The demo operates in mock mode using MSW (Mock Service Worker) without a backend connection.
> For actual data validation, install the package locally.

## Links

- [GitHub Repository](https://github.com/seadonggyun4/truthound-dashboard)
- [PyPI Package](https://pypi.org/project/truthound-dashboard/)
- [truthound Core Library](https://github.com/seadonggyun4/truthound)

## License

Apache License 2.0
