# truthound-dashboard

[![PyPI version](https://badge.fury.io/py/truthound-dashboard.svg)](https://pypi.org/project/truthound-dashboard/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A web-based data quality monitoring dashboard for [truthound](https://github.com/seadonggyun4/truthound).

[Documentation](https://truthound.netlify.app) | [Live Demo](https://truthound-dashboard.netlify.app) | [PyPI](https://pypi.org/project/truthound-dashboard/)

## Overview

truthound-dashboard provides a graphical interface for managing data sources, executing validations, tracking historical results, scheduling automated checks, and configuring notifications. It serves as an alternative to commercial data quality platforms.

## Feature Comparison with GX Cloud

| Feature | GX Cloud (Paid) | truthound-dashboard |
|---------|-----------------|---------------------|
| Data Source Management | Available | Available |
| Schema Learning | Available | Available |
| Validation Execution | Available | Available |
| Validation History | Available | Available |
| Scheduled Validations | Available | Available |
| Slack Notifications | Available | Available |
| Email Notifications | Available | Available |
| Webhook Notifications | Available | Available |
| Drift Detection | Available | Available |
| Data Profiling | Available | Available |
| Dark Mode | Available | Available |
| Multi-language (en/ko) | Not Available | Available |
| License | Commercial | Apache 2.0 |

## Requirements

- Python 3.11 or higher
- truthound >= 1.0.5

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

## Implemented Features

### Data Source Management
- Supported file formats: CSV, Parquet
- Supported databases: PostgreSQL, MySQL, Snowflake, BigQuery
- Connection validation

### Schema Management
- Automated schema generation using `th.learn`
- Manual schema editing in YAML format

### Validation
- On-demand validation execution using `th.check`
- Persistent storage of validation results
- Issue classification by severity (Critical, High, Medium, Low)

### Validation History
- Historical record of validation results
- Trend visualization

### Scheduling
- Cron-based scheduling using APScheduler
- Schedule controls: pause, resume, immediate execution

### Notifications
- Supported channels: Slack, Email, Webhook
- Configurable notification rules based on validation outcomes
- Notification delivery logs

### Drift Detection
- Dataset comparison using `th.compare`
- Column-level drift analysis

### Data Profiling
- Statistical profiling using `th.profile`
- Column-level statistics

### User Interface
- Light and dark theme support
- Internationalization: English, Korean

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
- i18next

## Development Setup

```bash
# Clone the repository
git clone https://github.com/seadonggyun4/truthound-dashboard
cd truthound-dashboard

# Install backend dependencies
pip install -e ".[dev]"

# Start the backend server
truthound serve --reload

# In a separate terminal, install frontend dependencies
cd frontend
npm install

# Start the frontend development server
npm run dev

# Alternative: run with mock API (backend not required)
npm run dev:mock
```

## Testing

```bash
# Run tests
pytest

# Run tests with coverage report
pytest --cov=truthound_dashboard
```

## Live Demo

A live demonstration is available at [https://truthound-dashboard.netlify.app](https://truthound-dashboard.netlify.app).

The demo instance operates using Mock Service Worker (MSW) with simulated data and does not require a backend connection.

## Documentation

Full documentation is available at [https://truthound.netlify.app](https://truthound.netlify.app).

- [Getting Started](./docs/getting-started.md)
- [Features](./docs/features.md)
- [API Reference](./docs/api.md)
- [Configuration](./docs/configuration.md)

## Related Projects

- [truthound](https://github.com/seadonggyun4/truthound) - Core data validation library
- [truthound-orchestration](https://github.com/seadonggyun4/truthound-orchestration) - Pipeline orchestration integration

## License

This project is licensed under the Apache License 2.0.
