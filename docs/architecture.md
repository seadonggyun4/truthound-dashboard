# System Architecture

This document presents a systematic exposition of the Truthound Dashboard architecture, encompassing the system design, inter-component interactions, and the underlying architectural design rationale that informed key engineering decisions.

## Overview

The Truthound Dashboard has been designed and implemented as a single-process application that consolidates web serving, API handling, task scheduling, and database operations into a unified runtime environment. This architectural decision was deliberately adopted to eliminate external dependencies such as Redis, Celery, or PostgreSQL, thereby achieving a zero-configuration deployment model that minimizes operational overhead and reduces deployment complexity.

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

The backend subsystem is composed of the following constituent components, each of which fulfills a well-defined responsibility within the overall system architecture.

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

The frontend subsystem has been constructed upon a modern single-page application architecture, leveraging the following technologies and frameworks.

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

The following directory hierarchy illustrates the organizational taxonomy of the codebase, reflecting the separation of concerns between backend services, frontend presentation, and supporting documentation.

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

All API endpoints are served under the following base URI, which establishes the versioned namespace for the RESTful interface.

```
http://localhost:8765/api/v1
```

### Endpoint Categories

The API surface area is organized into the following functional categories, each of which encapsulates a logically cohesive set of operations.

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
                                  — supports result_format (PHASE 1),
                                    catch_exceptions/max_retries (PHASE 5)
GET  /validations/{id}          Retrieve validation results
                                  — includes statistics (PHASE 2),
                                    validator_execution_summary (PHASE 4),
                                    exception_summary (PHASE 5)
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

## Architectural Design Rationale

The selection of constituent technologies was governed by the overarching principle of operational simplicity, wherein each component was evaluated against the criterion of whether it could be embedded within a single-process runtime without introducing external service dependencies.

### Selected Technology Stack

The following table enumerates the technologies that were selected for inclusion in the system architecture, together with the rationale underpinning each selection decision.

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Web Server | Uvicorn | Single-process ASGI server with excellent performance |
| API Framework | FastAPI | High-performance framework with automatic OpenAPI generation |
| Database | SQLite | Zero-configuration embedded database |
| Scheduler | APScheduler | Cron-compatible scheduling within a single process |
| Frontend | React Static | Pre-built static files for simplified deployment |

### Architectural Exclusion Rationale

Conversely, several widely adopted technologies were deliberately excluded from the architecture. The following table documents each exclusion together with its justification, demonstrating that these omissions represent conscious design decisions rather than oversights.

| Component | Rationale |
|-----------|-----------|
| Redis | SQLite provides sufficient functionality; eliminates external dependency |
| Celery | APScheduler meets scheduling requirements; reduces complexity |
| PostgreSQL | SQLite satisfies data persistence needs; maintains zero-configuration |
| WebSocket | HTTP polling provides adequate real-time functionality; reduces complexity |
| Prometheus/Grafana | Unnecessary for local deployment scenarios |

## Data Flow Topology

The following diagram illustrates the data flow topology through which user requests are propagated across the system's architectural layers. Requests are first subjected to schema validation at the API boundary, subsequently dispatched to the appropriate business logic handler, and ultimately routed to either the persistent storage layer or the truthound validation engine, depending on the nature of the operation.

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

## Truthound Core Engine Integration Architecture

The dashboard maintains a bidirectional integration with the Truthound core validation engine (v1.3.0), which has undergone a systematic five-phase enhancement programme. Each enhancement phase in the core library necessitated corresponding adaptations across the dashboard's backend adapter, result converter, Pydantic schema definitions, and frontend TypeScript type declarations. This section provides a formal specification of the integration architecture and its constituent components.

### Integration Layer Topology

The integration between the dashboard and the Truthound core engine is mediated by a layered adapter architecture, wherein each layer fulfils a well-defined translation responsibility:

```
Frontend (React/TypeScript)
  └─ ValidationRunOptions           ← TypeScript interface (PHASE 1/5 params)
        │
        ▼
  └─ POST /sources/{id}/validate    ← REST API boundary
        │
        ▼
Backend (FastAPI)
  └─ ValidationRunRequest           ← Pydantic request schema
        │
        ▼
  └─ ValidationService              ← Parameter propagation (services.py)
        │
        ▼
  └─ TruthoundAdapter.check()       ← Core engine invocation
        │
        ▼
  └─ th.check(**kwargs)             ← truthound Python API
        │
        ▼
  └─ TruthoundResultConverter       ← Domain object → dict translation
        │
        ▼
  └─ CheckResult                    ← Dashboard-internal dataclass
        │
        ▼
  └─ result_json (SQLite)           ← Persistent storage (JSON column)
        │
        ▼
  └─ ValidationResponse             ← Pydantic response schema
        │
        ▼
  └─ Validation (TypeScript)        ← Frontend consumption
```

### Phase-by-Phase Integration Specification

The following table enumerates the integration scope for each core engine enhancement phase, together with the specific dashboard files that were modified or extended:

| Phase | Core Enhancement | Dashboard Integration Scope | Modified Files |
|-------|-----------------|----------------------------|----------------|
| **PHASE 1** | Result Format System (4-level progressive disclosure) | `result_format`, `include_unexpected_rows`, `max_unexpected_rows` parameter propagation through all layers | `schemas/validation.py`, `truthound_adapter.py`, `services.py`, `api/validations.py`, `validations.ts`, `SourceDetail.tsx` |
| **PHASE 2** | Structured Results (`ValidationDetail`, `ReportStatistics`) | `ValidationDetailResult`, `ReportStatistics`, `ValidationIssue` schema extensions; converter rewrite | `converters/truthound.py`, `truthound_adapter.py`, `schemas/validation.py`, `validations.ts`, `Validations.tsx` |
| **PHASE 3** | Metric Deduplication (`SharedMetricStore`) | No changes required — internal optimisation transparent to API consumers | — |
| **PHASE 4** | DAG Execution (dependency-based conditional validator scheduling) | `ValidatorExecutionSummary`, `SkippedValidatorInfo`; history comparison considerations | `truthound_adapter.py`, `schemas/validation.py`, `validations.ts`, `services.py` |
| **PHASE 5** | Exception Isolation (3-tier fallback, auto-retry, circuit breaker) | `catch_exceptions`, `max_retries` parameter propagation; `ExceptionInfo`, `ExceptionSummary` schemas | `converters/truthound.py`, `truthound_adapter.py`, `schemas/validation.py`, `validations.ts`, `services.py`, `api/validations.py`, `SourceDetail.tsx` |

### Backward Compatibility Strategy

The integration adheres to a principled backward compatibility protocol that ensures uninterrupted service during incremental upgrades:

1. **Optional Field Declarations**: All fields introduced through the enhancement phases are declared as `Optional` with `None` default values in both Pydantic schemas and TypeScript interfaces.
2. **Pydantic Extra Ignore**: `model_config = ConfigDict(extra="ignore")` is applied to all schema classes that receive data from the core engine, ensuring forward compatibility with future Truthound versions.
3. **Defensive Attribute Access**: The `TruthoundResultConverter` employs `getattr(obj, "field", default)` patterns throughout, gracefully handling absent fields in older engine versions.
4. **Database Schema Stability**: No SQLAlchemy model changes were required; all new data is accommodated within the existing `result_json` JSON column, preserving schema continuity.

### Frontend Visualisation Components (PHASE 1–5)

The frontend implements dedicated panel components for each enhancement phase's data:

| Component | Phase | Functionality |
|-----------|-------|---------------|
| `IssueDetailPanel` | PHASE 2 | Renders `ValidationDetail` metrics (element count, unexpected percent, sample values) |
| `StatisticsPanel` | PHASE 2 | Visualises `ReportStatistics` with severity/column/validator breakdowns |
| `ExecutionSummaryPanel` | PHASE 4 | Displays executed/skipped/failed validator counts with skip reason details |
| `ExceptionSummaryPanel` | PHASE 5 | Presents exception statistics, retry rates, and circuit breaker status |
| `IssueCard` | PHASE 2/5 | Enhanced issue card with `ValidationDetail` expansion and `ExceptionInfo` badge |
| Advanced Options | PHASE 1/5 | Collapsible configuration section for `result_format`, `catch_exceptions`, `max_retries` |

## Security Architecture

### Credential Management

Connection credentials are subjected to symmetric encryption using the Fernet cryptographic scheme prior to their persistence in the SQLite database. The encryption key is automatically generated during initial system initialization and is stored at `~/.truthound/.key` with restricted file system permissions, thereby ensuring that sensitive credential material is not exposed in plaintext at rest.

### Data Isolation

Each Truthound Dashboard instance maintains a strictly isolated data directory (`~/.truthound` by default), thereby guaranteeing complete separation of state and configuration between multiple concurrent installations. This isolation boundary ensures that no cross-instance information leakage can occur.

## Scalability Analysis and Extension Points

The single-process architecture has been expressly optimized for individual workstation and small team deployment scenarios, where operational simplicity and minimal configuration overhead are prioritized. For enterprise-scale deployments necessitating horizontal scaling capabilities, the architecture has been designed with the following extension points to facilitate a graduated scaling trajectory:

1. **Load Balancing**: Multiple Truthound Dashboard instances may be deployed behind a reverse proxy to distribute request load across replicas.
2. **Shared Storage**: Migration to an external relational database can be undertaken to enable multi-instance state coordination and consistency.
3. **Message Queue Integration**: Optional integration with Celery or equivalent distributed task processing frameworks can be introduced to support asynchronous workload distribution.

## References

- [truthound Core Library](https://github.com/seadonggyun4/truthound)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
