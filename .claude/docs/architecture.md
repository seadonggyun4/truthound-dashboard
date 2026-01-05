# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    truthound-dashboard                           │
│                    (Single Process)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  $ truthound serve                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                     Uvicorn                              │    │
│  │                  (ASGI Server)                           │    │
│  └──────────────────────┬──────────────────────────────────┘    │
│                         │                                        │
│         ┌───────────────┼───────────────┐                       │
│         │               │               │                       │
│         ▼               ▼               ▼                       │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐                 │
│  │  FastAPI  │   │   React   │   │APScheduler│                 │
│  │   (API)   │   │  (Static) │   │ (Cron)    │                 │
│  └─────┬─────┘   └───────────┘   └─────┬─────┘                 │
│        │                               │                        │
│        └───────────────┬───────────────┘                        │
│                        │                                        │
│                        ▼                                        │
│         ┌─────────────────────────────┐                        │
│         │          SQLite             │                        │
│         │    (~/.truthound/dashboard.db)                       │
│         └─────────────────────────────┘                        │
│                        │                                        │
│                        ▼                                        │
│         ┌─────────────────────────────┐                        │
│         │        truthound            │                        │
│         │      (PyPI Package)         │                        │
│         │  th.check, th.profile,      │                        │
│         │  th.learn, th.compare       │                        │
│         └─────────────────────────────┘                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### Backend Components

| Component | Technology | Role | File Location |
|-----------|------------|------|---------------|
| **CLI** | Typer | `truthound serve` 명령어 | `cli.py` |
| **Web Server** | Uvicorn | ASGI 서버, 단일 프로세스 | `main.py` |
| **API** | FastAPI | REST API, 정적 파일 서빙 | `api/` |
| **Database** | SQLite + aiosqlite | 메타데이터, 결과 저장 | `db/` |
| **ORM** | SQLAlchemy 2.0 | 비동기 DB 작업 | `db/models.py` |
| **Scheduler** | APScheduler | Cron 기반 스케줄링 | `core/scheduler.py` |
| **Core Engine** | truthound | 데이터 품질 검증 | `core/truthound_adapter.py` |
| **Notifications** | httpx, aiosmtplib | Slack/Email/Webhook | `core/notifier.py` |
| **Schemas** | Pydantic 2.x | Request/Response 검증 | `schemas/` |

### Frontend Components

| Component | Technology | Role |
|-----------|------------|------|
| **Framework** | React 18 | SPA |
| **Build** | Vite | 빠른 빌드 |
| **Styling** | TailwindCSS | 유틸리티 CSS |
| **UI** | shadcn/ui | Radix 기반 컴포넌트 |
| **State** | Zustand | 상태 관리 |
| **Charts** | Recharts | 트렌드 시각화 |
| **Router** | React Router 6 | SPA 라우팅 |
| **Forms** | React Hook Form + Zod | 폼 처리 |

## Directory Structure

```
src/truthound_dashboard/
├── __init__.py
├── __main__.py               # python -m truthound_dashboard
├── cli.py                    # CLI (truthound serve)
├── main.py                   # FastAPI app
├── config.py                 # Settings
│
├── api/
│   ├── __init__.py
│   ├── router.py             # API router
│   ├── sources.py            # Data sources CRUD
│   ├── rules.py              # Rules CRUD
│   ├── validations.py        # Run validations
│   ├── schedules.py          # Schedule management
│   ├── profiles.py           # Data profiling
│   ├── notifications.py      # Notification settings
│   └── health.py             # Health check
│
├── core/
│   ├── __init__.py
│   ├── truthound_adapter.py  # truthound 패키지 래퍼
│   ├── scheduler.py          # APScheduler 설정
│   ├── notifier.py           # Slack/Email/Webhook
│   └── exceptions.py         # Custom exceptions
│
├── db/
│   ├── __init__.py
│   ├── database.py           # SQLite 연결
│   ├── models.py             # SQLAlchemy models
│   └── migrations.py         # Auto migration
│
├── schemas/
│   ├── __init__.py
│   ├── source.py              # SourceCreate, SourceResponse, etc.
│   └── validation.py          # ValidationResponse, ValidationIssue, etc.
                               # ValidationIssue: column, issue_type, count, severity, details
│
└── static/                   # React 빌드 결과물
    ├── index.html
    └── assets/
```

## Database Schema

```sql
-- Data Sources
CREATE TABLE sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- file, postgresql, mysql, snowflake, bigquery
    config JSON NOT NULL,  -- connection details (encrypted)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Learned Schema (per source)
-- truthound th.learn() returns Schema with columns, row_count, version
-- Each ColumnSchema has: name, dtype, nullable, unique, min_value, max_value, etc.
CREATE TABLE schemas (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id),
    schema_yaml TEXT NOT NULL,  -- YAML representation for display/editing
    schema_json JSON,  -- Schema as dict for processing
    row_count INTEGER,  -- row count when schema was learned
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Validation Rules (per source) - optional custom rules
-- Note: truthound uses 'validators' (list) and 'schema' (path/object)
CREATE TABLE rules (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id),
    rules_yaml TEXT NOT NULL,  -- YAML format for custom schema overrides
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Validation Results
-- truthound Report contains: passed, has_critical, has_high, total_issues, issues
-- Each issue has: column, issue_type, count, severity, details, expected, actual
CREATE TABLE validations (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id),
    status TEXT NOT NULL,  -- running, success, failed, error
    passed BOOLEAN,  -- whether validation passed (no issues found)
    has_critical BOOLEAN,  -- whether any critical severity issues exist
    has_high BOOLEAN,  -- whether any high severity issues exist
    total_issues INTEGER,  -- total number of issues found
    critical_issues INTEGER,  -- count of critical issues
    high_issues INTEGER,  -- count of high issues
    row_count INTEGER,  -- number of rows in the data
    column_count INTEGER,  -- number of columns in the data
    result_json JSON,  -- Full result from truthound (includes issues array)
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Schedules
CREATE TABLE schedules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source_id TEXT REFERENCES sources(id),  -- NULL = all sources
    cron_expression TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    notify_on_failure BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notification Channels
CREATE TABLE notification_channels (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,  -- slack, email, webhook
    config JSON NOT NULL,  -- channel-specific config
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notification Rules
CREATE TABLE notification_rules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    condition TEXT NOT NULL,  -- validation_failed, pass_rate_below, etc.
    condition_value TEXT,  -- e.g., "90" for pass_rate_below
    channel_ids JSON NOT NULL,  -- array of channel IDs
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Profiles (cached)
CREATE TABLE profiles (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id),
    profile_json JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Settings
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value JSON NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Design

### Base URL
```
http://localhost:8765/api/v1
```

### Endpoints

```
── Health ──────────────────────────────────────────────────────────
GET  /health                    서버 상태 확인

── Sources ─────────────────────────────────────────────────────────
GET  /sources                   데이터 소스 목록
POST /sources                   데이터 소스 추가
GET  /sources/{id}              데이터 소스 상세
PUT  /sources/{id}              데이터 소스 수정
DEL  /sources/{id}              데이터 소스 삭제
POST /sources/{id}/test         연결 테스트
GET  /sources/{id}/tables       테이블 목록 (DB 소스)

── Schema & Rules ──────────────────────────────────────────────────
GET  /sources/{id}/schema       스키마 조회 (th.learn 결과)
PUT  /sources/{id}/schema       스키마 저장
GET  /sources/{id}/rules        커스텀 규칙 조회
PUT  /sources/{id}/rules        커스텀 규칙 저장
POST /sources/{id}/rules/import YAML 파일에서 import
GET  /sources/{id}/rules/export YAML로 export

── Validations ─────────────────────────────────────────────────────
POST /sources/{id}/validate     검증 실행 (th.check)
                                - validators: list[str] (선택)
                                - schema: str (스키마 경로, 선택)
                                - auto_schema: bool (자동 스키마, 선택)
GET  /validations/{id}          검증 결과 조회
GET  /validations/{id}/status   검증 진행 상태 (폴링)
GET  /sources/{id}/validations  검증 히스토리

── Profiles ────────────────────────────────────────────────────────
POST /sources/{id}/profile      프로파일링 실행 (th.profile)
                                - ProfileReport: source, row_count, column_count, size_bytes, columns
GET  /sources/{id}/profile      최근 프로파일 조회
POST /sources/{id}/learn        스키마 자동 생성 (th.learn)
                                - Schema: columns (ColumnSchema), row_count, version

── Drift ───────────────────────────────────────────────────────────
POST /drift/compare             두 소스 비교 (th.compare)
                                - DriftReport: has_drift, has_high_drift, columns, drifted_columns
GET  /drift/{id}                비교 결과 조회

── Schedules ───────────────────────────────────────────────────────
GET  /schedules                 스케줄 목록
POST /schedules                 스케줄 생성
GET  /schedules/{id}            스케줄 상세
PUT  /schedules/{id}            스케줄 수정
DEL  /schedules/{id}            스케줄 삭제
POST /schedules/{id}/pause      스케줄 일시정지
POST /schedules/{id}/resume     스케줄 재개
POST /schedules/{id}/run        즉시 실행

── Notifications ───────────────────────────────────────────────────
GET  /notifications/channels    알림 채널 목록
PUT  /notifications/slack       Slack 설정
PUT  /notifications/email       Email 설정
PUT  /notifications/webhook     Webhook 설정
POST /notifications/test        테스트 알림 발송
GET  /notifications/rules       알림 규칙 목록
POST /notifications/rules       알림 규칙 추가

── Settings ────────────────────────────────────────────────────────
GET  /settings                  설정 조회
PUT  /settings                  설정 저장
```

### Response Format

```json
// Success
{
  "success": true,
  "data": { ... }
}

// Error
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid source configuration",
    "details": [...]
  }
}

// Pagination
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

## Design Principles

### What We Include

| Component | Technology | Why |
|-----------|------------|-----|
| Web Server | Uvicorn | 단일 프로세스 ASGI |
| API | FastAPI | 고성능, 자동 OpenAPI |
| Database | SQLite | Zero-Config, 임베디드 |
| Scheduler | APScheduler | Cron, 단일 프로세스 |
| Frontend | React Static | 빌드 후 정적 파일 |

### What We Exclude (Intentionally)

| Excluded | Why |
|----------|-----|
| Redis | SQLite로 충분, 외부 의존성 제거 |
| Celery | APScheduler로 충분, 단순화 |
| PostgreSQL | SQLite로 충분, Zero-Config |
| WebSocket | HTTP 폴링으로 충분, 복잡성 제거 |
| Prometheus/Grafana | 로컬 솔루션에 불필요 |
| Kubernetes | 로컬 설치형, 불필요 |

## Security Model

로컬 설치형 솔루션이므로 단순한 보안 모델 사용:

```python
class Settings(BaseSettings):
    # 기본 설정
    data_dir: str = "~/.truthound"
    port: int = 8765
    host: str = "127.0.0.1"  # 로컬만 바인딩

    # 선택적 인증 (기본 비활성화)
    auth_enabled: bool = False
    auth_password: str | None = None

    class Config:
        env_prefix = "TRUTHOUND_"
```

```bash
# 패스워드 없이 (기본)
truthound serve

# 패스워드 보호 활성화
TRUTHOUND_AUTH_ENABLED=true TRUTHOUND_AUTH_PASSWORD=secret truthound serve
```

## Data Flow

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
│    API      │ ← Business logic
│  Handlers   │
└─────┬───────┘
      │
      ├──────────────────┐
      │                  │
      ▼                  ▼
┌───────────┐     ┌────────────┐
│  SQLite   │     │ truthound  │ ← Data validation
│    DB     │     │  adapter   │
└───────────┘     └────────────┘
                        │
                        ▼
                  ┌───────────┐
                  │  Data     │ ← CSV, Parquet, DB
                  │  Sources  │
                  └───────────┘
```
