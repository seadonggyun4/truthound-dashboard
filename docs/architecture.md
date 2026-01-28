# System Architecture

This document provides a comprehensive overview of the Truthound Dashboard architecture, detailing the system design, component interactions, and underlying design principles.

## Overview

Truthound Dashboard is engineered as a single-process application that consolidates web serving, API handling, task scheduling, and database operations into a unified runtime environment. This architectural decision eliminates external dependencies such as Redis, Celery, or PostgreSQL, thereby achieving a zero-configuration deployment model.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Truthound Dashboard                          │
│                    (Single Process Architecture)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  $ truthound serve                                              │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                     Uvicorn                              │   │
│  │                  (ASGI Server)                           │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │                                       │
│         ┌───────────────┼───────────────┐                      │
│         │               │               │                      │
│         ▼               ▼               ▼                      │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐                │
│  │  FastAPI  │   │   React   │   │APScheduler│                │
│  │   (API)   │   │  (Static) │   │  (Cron)   │                │
│  └─────┬─────┘   └───────────┘   └─────┬─────┘                │
│        │                               │                       │
│        └───────────────┬───────────────┘                       │
│                        │                                       │
│                        ▼                                       │
│         ┌─────────────────────────────┐                       │
│         │          SQLite             │                       │
│         │   (~/.truthound/dashboard.db)                       │
│         └─────────────────────────────┘                       │
│                        │                                       │
│                        ▼                                       │
│         ┌─────────────────────────────┐                       │
│         │        truthound            │                       │
│         │      (Core Library)         │                       │
│         │  th.check, th.profile,      │                       │
│         │  th.learn, th.compare,      │                       │
│         │  th.scan, th.mask           │                       │
│         └─────────────────────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Component Specifications

### Backend Components

| Component | Technology | Responsibility | Location |
|-----------|------------|----------------|----------|
| **CLI** | Typer | Command-line interface for `truthound serve` and `truthound translate` | `cli.py` |
| **Web Server** | Uvicorn | ASGI server providing single-process execution | `main.py` |
| **API Layer** | FastAPI | REST API endpoints and static file serving | `api/` |
| **Database** | SQLite + aiosqlite | Persistent storage for metadata and validation results | `db/` |
| **ORM** | SQLAlchemy 2.0 | Asynchronous database operations | `db/models.py` |
| **Scheduler** | APScheduler | Cron-based task scheduling | `core/scheduler.py` |
| **Core Engine** | truthound | Data quality validation operations | `core/truthound_adapter.py` |
| **Notifications** | httpx, aiosmtplib | Multi-channel alert delivery (Slack, Email, Webhook) | `core/notifications/` |
| **Cache** | In-memory | API response caching for performance optimization | `core/cache.py` |
| **Security** | Fernet | Symmetric encryption for connection credentials | `core/encryption.py` |
| **Schemas** | Pydantic 2.x | Request and response validation | `schemas/` |
| **Translation** | AI Providers | Multi-language translation CLI | `translate/` |
| **Enterprise Sampling** | truthound 1.2.10+ | Large-scale sampling strategies (Block, Multi-Stage, Column-Aware, Progressive) | `core/enterprise_sampling.py` |

### Frontend Components

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| **Framework** | React 18 | Single-page application architecture |
| **Build System** | Vite | Development server and production bundling |
| **Styling** | TailwindCSS | Utility-first CSS framework |
| **UI Components** | shadcn/ui | Radix-based accessible component library |
| **State Management** | Zustand | Lightweight reactive state management |
| **Data Visualization** | Recharts | Trend analysis and charting |
| **Routing** | React Router 6 | Client-side navigation |
| **Internationalization** | Intlayer | Type-safe multi-language support |
| **Theming** | Zustand + Tailwind | Dark and light mode implementation |
| **Lineage Visualization** | ReactFlow, Cytoscape, Mermaid | Data lineage graph rendering |

## Directory Structure

```
truthound-dashboard/
├── src/truthound_dashboard/     # Backend (FastAPI)
│   ├── __init__.py
│   ├── __main__.py              # Entry point for python -m
│   ├── cli.py                   # CLI commands
│   ├── main.py                  # FastAPI application
│   ├── config.py                # Configuration management
│   │
│   ├── api/                     # REST API endpoints
│   │   ├── sources.py           # Data source CRUD operations
│   │   ├── schemas.py           # Schema management (th.learn)
│   │   ├── validations.py       # Validation execution
│   │   ├── schedules.py         # Schedule management
│   │   ├── notifications.py     # Notification channels and rules
│   │   ├── notifications_advanced.py  # Routing, deduplication, throttling
│   │   ├── glossary.py          # Business glossary API
│   │   ├── catalog.py           # Data catalog API
│   │   ├── collaboration.py     # Comments and activities API
│   │   ├── anomaly.py           # ML-based anomaly detection
│   │   ├── lineage.py           # Data lineage tracking
│   │   ├── reports.py           # Multi-format report generation
│   │   ├── versioning.py        # Result versioning
│   │   ├── rule_suggestions.py  # AI-powered rule generation
│   │   ├── model_monitoring.py  # ML model performance monitoring
│   │   ├── maintenance.py       # Data retention and cleanup
│   │   ├── plugins.py           # Plugin marketplace
│   │   ├── triggers.py          # Event trigger system
│   │   ├── quality_reporter.py  # Quality scoring and reporting
│   │   ├── enterprise_sampling.py  # Enterprise-scale sampling API
│   │   └── health.py            # Health check endpoint
│   │
│   ├── core/                    # Business logic layer
│   │   ├── truthound_adapter.py # truthound library wrapper
│   │   ├── services.py          # Service layer implementation
│   │   ├── scheduler.py         # APScheduler configuration
│   │   ├── cache.py             # In-memory caching
│   │   ├── encryption.py        # Credential encryption
│   │   ├── maintenance.py       # Database cleanup operations
│   │   ├── versioning.py        # Result versioning logic
│   │   ├── notifications/       # Notification subsystem
│   │   │   ├── routing/         # Rule-based message routing
│   │   │   ├── deduplication/   # Duplicate notification prevention
│   │   │   ├── throttling/      # Rate limiting implementation
│   │   │   └── escalation/      # Multi-level alert escalation
│   │   ├── reporters/           # Report generation engines
│   │   │   ├── csv_reporter.py
│   │   │   ├── json_reporter.py
│   │   │   ├── markdown_reporter.py
│   │   │   ├── pdf_reporter.py
│   │   │   └── junit_reporter.py
│   │   ├── quality_reporter.py  # Quality scoring service
│   │   ├── enterprise_sampling.py  # Enterprise-scale sampling strategies
│   │   └── phase5/              # Glossary and catalog services
│   │
│   ├── db/                      # Database layer
│   │   ├── database.py          # SQLite connection management
│   │   ├── models.py            # SQLAlchemy model definitions
│   │   └── repository.py        # Data access layer
│   │
│   ├── schemas/                 # Pydantic model definitions
│   │   ├── source.py
│   │   ├── validation.py
│   │   ├── drift.py
│   │   ├── glossary.py
│   │   ├── catalog.py
│   │   ├── enterprise_sampling.py  # Enterprise sampling request/response models
│   │   └── validators/          # 150+ validator definitions
│   │
│   ├── translate/               # AI translation subsystem
│   │   ├── translator.py        # Translation orchestration
│   │   ├── config_updater.py    # Intlayer configuration updater
│   │   └── providers/           # AI provider implementations
│   │       ├── openai.py
│   │       ├── anthropic.py
│   │       ├── ollama.py
│   │       └── mistral.py
│   │
│   └── static/                  # React build output
│
├── frontend/                    # React source code
│   ├── src/
│   │   ├── pages/               # Page components
│   │   ├── components/          # UI components
│   │   ├── api/                 # API client
│   │   ├── hooks/               # Custom React hooks
│   │   ├── stores/              # Zustand state stores
│   │   ├── content/             # Intlayer translation files
│   │   ├── lib/                 # Utility functions
│   │   ├── providers/           # React context providers
│   │   └── types/               # TypeScript type definitions
│   └── intlayer.config.ts       # Intlayer configuration
│
└── docs/                        # Documentation
```

## API Design

### Base URL

```
http://localhost:8765/api/v1
```

### Endpoint Categories

#### Health Monitoring
```
GET  /health                    Server status verification
```

#### Data Source Management
```
GET  /sources                   List all data sources
POST /sources                   Create a new data source
GET  /sources/{id}              Retrieve source details
PUT  /sources/{id}              Update source configuration
DEL  /sources/{id}              Delete a data source
POST /sources/{id}/test         Test connection validity
```

#### Validation Operations
```
POST /sources/{id}/validate     Execute validation (th.check)
GET  /validations/{id}          Retrieve validation results
GET  /sources/{id}/validations  Retrieve validation history
```

#### Data Profiling
```
POST /sources/{id}/profile      Execute data profiling (th.profile)
POST /sources/{id}/learn        Generate schema automatically (th.learn)
```

#### Drift Detection
```
POST /drift/compare             Compare two data sources (th.compare)
```

#### Validator Registry
```
GET  /validators                List 150+ available validators
```

#### Privacy Operations
```
POST /scans/sources/{id}/scan   Execute PII scanning (th.scan)
POST /masks/sources/{id}/mask   Execute data masking (th.mask)
```

#### Schedule Management
```
GET/POST /schedules             Manage scheduled validations
```

#### Notification System
```
GET/POST /notifications/channels    Manage notification channels
GET/POST /notifications/rules       Manage notification rules
```

#### Advanced Features
```
GET/POST /anomaly               ML-based anomaly detection
GET/POST /lineage               Data lineage management
GET/POST /glossary/terms        Business glossary
GET/POST /catalog/assets        Data catalog
GET/POST /reports               Report generation
GET/POST /model-monitoring      ML model monitoring
GET/POST /plugins               Plugin management
GET/POST /quality/*             Quality scoring and reporting
GET/POST /sampling/*            Enterprise sampling operations
```

## Design Principles

### Included Components

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Web Server | Uvicorn | Single-process ASGI server with excellent performance |
| API Framework | FastAPI | High-performance framework with automatic OpenAPI generation |
| Database | SQLite | Zero-configuration embedded database |
| Scheduler | APScheduler | Cron-compatible scheduling within a single process |
| Frontend | React Static | Pre-built static files for simplified deployment |

### Intentionally Excluded Components

| Component | Rationale |
|-----------|-----------|
| Redis | SQLite provides sufficient functionality; eliminates external dependency |
| Celery | APScheduler meets scheduling requirements; reduces complexity |
| PostgreSQL | SQLite satisfies data persistence needs; maintains zero-configuration |
| WebSocket | HTTP polling provides adequate real-time functionality; reduces complexity |
| Prometheus/Grafana | Unnecessary for local deployment scenarios |

## Data Flow Architecture

```
User Request
     │
     ▼
┌─────────────┐
│   FastAPI   │ ← Request validation (Pydantic)
└─────┬───────┘
      │
      ▼
┌─────────────┐
│    API      │ ← Business logic execution
│  Handlers   │
└─────┬───────┘
      │
      ├──────────────────┐
      │                  │
      ▼                  ▼
┌───────────┐     ┌────────────┐
│  SQLite   │     │ truthound  │ ← Data validation engine
│    DB     │     │  adapter   │
└───────────┘     └────────────┘
                        │
                        ▼
                  ┌───────────┐
                  │   Data    │ ← CSV, Parquet, databases
                  │  Sources  │
                  └───────────┘
```

## Security Considerations

### Credential Management

Connection credentials are encrypted using Fernet symmetric encryption before storage in the SQLite database. The encryption key is automatically generated and stored in `~/.truthound/.key` with restricted file permissions.

### Data Isolation

Each Truthound Dashboard instance maintains an isolated data directory (`~/.truthound` by default), ensuring complete separation between multiple installations.

## Scalability Characteristics

The single-process architecture is optimized for individual workstation and small team deployments. For enterprise-scale deployments requiring horizontal scaling, the architecture can be extended through:

1. **Load Balancing**: Multiple Truthound Dashboard instances behind a reverse proxy
2. **Shared Storage**: External database migration for multi-instance coordination
3. **Message Queue Integration**: Optional Celery integration for distributed task processing

## References

- [truthound Core Library](https://github.com/seadonggyun4/truthound)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
