# Phase 4: Production Ready (v1.0.0)

## Goal

안정화, 성능 최적화, 문서화, 보안 강화 - 프로덕션 배포 준비 완료

## Prerequisites

- Phase 3 완료 (알림 시스템 동작)
- 모든 핵심 기능 구현 완료

---

## Task 1: Performance Optimization

### 1.1 Database Optimization

**인덱스 추가**

```python
# src/truthound_dashboard/db/models.py

from sqlalchemy import Index

class Validation(Base):
    # ... existing fields ...

    __table_args__ = (
        Index('idx_validations_source_created', 'source_id', 'created_at'),
        Index('idx_validations_status', 'status'),
        Index('idx_validations_source_status', 'source_id', 'status'),
    )


class NotificationLog(Base):
    # ... existing fields ...

    __table_args__ = (
        Index('idx_notification_logs_channel', 'channel_id'),
        Index('idx_notification_logs_created', 'created_at'),
    )
```

**데이터 정리 작업**

```python
# src/truthound_dashboard/core/maintenance.py
"""Database maintenance tasks."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import delete, select

from ..db.database import get_db
from ..db.models import NotificationLog, Profile, Validation


async def cleanup_old_validations(days: int = 90):
    """Remove validation results older than specified days."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    async with get_db() as db:
        await db.execute(
            delete(Validation).where(Validation.created_at < cutoff)
        )


async def cleanup_old_profiles(keep_per_source: int = 5):
    """Keep only the most recent profiles per source."""
    async with get_db() as db:
        # Get all source IDs
        from ..db.models import Source
        sources = await db.execute(select(Source.id))

        for (source_id,) in sources:
            # Get profiles to keep
            keep_result = await db.execute(
                select(Profile.id)
                .where(Profile.source_id == source_id)
                .order_by(Profile.created_at.desc())
                .limit(keep_per_source)
            )
            keep_ids = [row[0] for row in keep_result]

            if keep_ids:
                await db.execute(
                    delete(Profile)
                    .where(Profile.source_id == source_id)
                    .where(Profile.id.not_in(keep_ids))
                )


async def cleanup_notification_logs(days: int = 30):
    """Remove notification logs older than specified days."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    async with get_db() as db:
        await db.execute(
            delete(NotificationLog).where(NotificationLog.created_at < cutoff)
        )


async def vacuum_database():
    """Reclaim space from deleted records."""
    from ..db.database import get_engine

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute("VACUUM")
```

**정기 정리 스케줄 추가**

```python
# src/truthound_dashboard/core/scheduler.py 에 추가

def schedule_maintenance(self):
    """Schedule database maintenance tasks."""
    from .maintenance import (
        cleanup_old_validations,
        cleanup_notification_logs,
        vacuum_database,
    )

    # Daily cleanup at 3 AM
    self.scheduler.add_job(
        cleanup_old_validations,
        trigger=CronTrigger.from_crontab("0 3 * * *"),
        id="maintenance_validations",
        replace_existing=True,
    )

    self.scheduler.add_job(
        cleanup_notification_logs,
        trigger=CronTrigger.from_crontab("0 3 * * *"),
        id="maintenance_logs",
        replace_existing=True,
    )

    # Weekly vacuum on Sunday at 4 AM
    self.scheduler.add_job(
        vacuum_database,
        trigger=CronTrigger.from_crontab("0 4 * * 0"),
        id="maintenance_vacuum",
        replace_existing=True,
    )
```

### 1.2 API Response Caching

```python
# src/truthound_dashboard/core/cache.py
"""Simple in-memory cache."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any


class SimpleCache:
    """Thread-safe in-memory cache with TTL."""

    def __init__(self):
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        async with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if datetime.utcnow() < expiry:
                    return value
                del self._cache[key]
        return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 60):
        """Set value in cache with TTL."""
        async with self._lock:
            expiry = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            self._cache[key] = (value, expiry)

    async def delete(self, key: str):
        """Delete value from cache."""
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self):
        """Clear all cached values."""
        async with self._lock:
            self._cache.clear()


# Singleton
_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """Get cache instance."""
    return _cache
```

**캐시 적용 예시**

```python
# src/truthound_dashboard/api/sources.py

from ..core.cache import get_cache

@router.get("", response_model=SourceListResponse)
async def list_sources():
    """List all data sources."""
    cache = get_cache()

    # Try cache first
    cached = await cache.get("sources_list")
    if cached:
        return SourceListResponse(data=cached)

    async with get_db() as db:
        result = await db.execute(select(Source).order_by(Source.created_at.desc()))
        sources = result.scalars().all()
        data = [SourceResponse.model_validate(s) for s in sources]

        # Cache for 30 seconds
        await cache.set("sources_list", data, ttl_seconds=30)

        return SourceListResponse(data=data)


# Invalidate cache on create/update/delete
@router.post("", response_model=SourceResponse)
async def create_source(source: SourceCreate):
    # ... create source ...
    await get_cache().delete("sources_list")
    return ...
```

### 1.3 Large Dataset Handling

truthound uses DataSource with sampling for large datasets. The dashboard should pre-sample data before calling validation.

```python
# src/truthound_dashboard/core/truthound_adapter.py 개선

async def check_with_sampling(
    self,
    data: str,
    validators: list[str] | None = None,
    sample_size: int | None = None,
) -> dict[str, Any]:
    """Run validation with optional pre-sampling for large datasets.

    Note: truthound's th.check() does not have a built-in sample parameter.
    For large datasets, use truthound DataSource with sampling:

        from truthound.datasources import get_datasource
        ds = get_datasource(data)
        if ds.needs_sampling():
            ds = ds.sample(n=sample_size)
        report = th.check(source=ds, validators=validators)

    For simple file-based sources, we sample using polars directly.

    Args:
        data: Data source path (first param of th.check is 'data', not 'source').
        validators: Optional list of validator names.
        sample_size: Optional sample size for large datasets.
    """
    from ..config import get_settings
    import polars as pl

    settings = get_settings()
    sample = sample_size or settings.sample_size

    # Check file size first
    from pathlib import Path
    if Path(data).exists():
        size_mb = Path(data).stat().st_size / (1024 * 1024)
        if size_mb > 100:  # Over 100MB, pre-sample the data
            # Load with polars and sample
            if data.endswith('.csv'):
                df = pl.read_csv(data)
            elif data.endswith('.parquet'):
                df = pl.read_parquet(data)
            else:
                df = pl.read_csv(data)  # fallback

            if len(df) > sample:
                df = df.sample(n=sample, seed=42)

            # Run validation on sampled DataFrame
            # th.check() first positional param is 'data'
            func = partial(
                th.check,
                df,
                validators=validators,
            )
        else:
            func = partial(th.check, data, validators=validators)
    else:
        func = partial(th.check, data, validators=validators)

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(self._executor, func)

    return self._convert_check_result(result)
```

---

## Task 2: Error Handling

### 2.1 Custom Exceptions

```python
# src/truthound_dashboard/core/exceptions.py
"""Custom exceptions."""

from __future__ import annotations


class TruthoundDashboardError(Exception):
    """Base exception for truthound-dashboard."""

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class SourceNotFoundError(TruthoundDashboardError):
    """Source not found."""

    def __init__(self, source_id: str):
        super().__init__(
            message=f"Source not found: {source_id}",
            code="SOURCE_NOT_FOUND",
        )


class ValidationError(TruthoundDashboardError):
    """Validation failed."""

    def __init__(self, message: str):
        super().__init__(message=message, code="VALIDATION_ERROR")


class ConnectionError(TruthoundDashboardError):
    """Database connection failed."""

    def __init__(self, source_type: str, details: str):
        super().__init__(
            message=f"Failed to connect to {source_type}: {details}",
            code="CONNECTION_ERROR",
        )


class ScheduleError(TruthoundDashboardError):
    """Schedule operation failed."""

    def __init__(self, message: str):
        super().__init__(message=message, code="SCHEDULE_ERROR")


class NotificationError(TruthoundDashboardError):
    """Notification delivery failed."""

    def __init__(self, channel_type: str, details: str):
        super().__init__(
            message=f"Failed to send {channel_type} notification: {details}",
            code="NOTIFICATION_ERROR",
        )
```

### 2.2 Global Exception Handler

```python
# src/truthound_dashboard/api/error_handlers.py
"""Global error handlers."""

from __future__ import annotations

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..core.exceptions import TruthoundDashboardError

logger = logging.getLogger(__name__)


def setup_error_handlers(app: FastAPI):
    """Configure global error handlers."""

    @app.exception_handler(TruthoundDashboardError)
    async def handle_dashboard_error(
        request: Request, exc: TruthoundDashboardError
    ) -> JSONResponse:
        """Handle custom dashboard errors."""
        logger.warning(f"Dashboard error: {exc.code} - {exc.message}")

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                },
            },
        )

    @app.exception_handler(Exception)
    async def handle_generic_error(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected errors."""
        logger.error(f"Unexpected error: {exc}\n{traceback.format_exc()}")

        # Don't expose internal errors to users
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred. Please try again later.",
                },
            },
        )
```

### 2.3 Apply to Main App

```python
# src/truthound_dashboard/main.py

from .api.error_handlers import setup_error_handlers

# After creating app
app = FastAPI(...)

# Setup error handlers
setup_error_handlers(app)
```

### 2.4 User-Friendly Error Messages

```python
# src/truthound_dashboard/core/error_messages.py
"""User-friendly error messages."""

ERROR_MESSAGES = {
    "SOURCE_NOT_FOUND": {
        "en": "The data source could not be found. It may have been deleted.",
        "ko": "데이터 소스를 찾을 수 없습니다. 삭제되었을 수 있습니다.",
    },
    "VALIDATION_ERROR": {
        "en": "Validation failed. Please check your rules configuration.",
        "ko": "검증에 실패했습니다. 규칙 설정을 확인해주세요.",
    },
    "CONNECTION_ERROR": {
        "en": "Could not connect to the database. Please verify your connection settings.",
        "ko": "데이터베이스에 연결할 수 없습니다. 연결 설정을 확인해주세요.",
    },
    "SCHEDULE_ERROR": {
        "en": "Schedule operation failed. Please check the cron expression.",
        "ko": "스케줄 작업에 실패했습니다. Cron 표현식을 확인해주세요.",
    },
    "NOTIFICATION_ERROR": {
        "en": "Failed to send notification. Please check your channel configuration.",
        "ko": "알림 발송에 실패했습니다. 채널 설정을 확인해주세요.",
    },
}


def get_error_message(code: str, lang: str = "en") -> str:
    """Get localized error message."""
    messages = ERROR_MESSAGES.get(code, {})
    return messages.get(lang, messages.get("en", "An error occurred"))
```

---

## Task 3: Documentation

### 3.1 README.md

```markdown
# truthound-dashboard

> Open-source data quality dashboard - GX Cloud alternative

[![PyPI version](https://badge.fury.io/py/truthound-dashboard.svg)](https://badge.fury.io/py/truthound-dashboard)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Truthound Dashboard provides all the premium features of [GX Cloud](https://greatexpectations.io/gx-cloud/) **for free**:

| Feature | GX Cloud | truthound-dashboard |
|---------|----------|---------------------|
| UI Rule Editor | ✅ Paid | ✅ Free |
| Validation History | ✅ Paid | ✅ Free |
| Scheduled Validations | ✅ Paid | ✅ Free |
| Slack/Email Alerts | ✅ Paid | ✅ Free |
| Auto Rule Generation | ✅ Paid | ✅ Free |
| Drift Detection | ✅ Paid | ✅ Free |
| Unlimited Users | Team $$$ | ✅ Free |
| Price | $$$$/month | $0 forever |

## Quick Start

```bash
# Install
pip install truthound-dashboard

# Run (opens browser automatically)
truthound serve
```

That's it! Dashboard runs at http://localhost:8765

## Features

### Data Sources
Connect to CSV, Parquet, PostgreSQL, MySQL, Snowflake, BigQuery

### Visual Rule Editor
Create validation rules without writing code

### Validation History
Track data quality trends over time

### Scheduled Validations
Cron-based automatic validation

### Notifications
Get alerts via Slack, Email, or Webhook when validations fail

### Auto Rule Generation
Let AI suggest rules based on your data

### Drift Detection
Compare datasets to detect changes

## CLI Options

```bash
truthound serve                    # Start on default port 8765
truthound serve --port 9000        # Custom port
truthound serve --host 0.0.0.0     # Allow external access
truthound serve --no-browser       # Don't open browser
truthound serve --reload           # Development mode
truthound serve --data-dir /path   # Custom data directory
```

## Configuration

Environment variables (optional):

```bash
TRUTHOUND_PORT=8765
TRUTHOUND_HOST=127.0.0.1
TRUTHOUND_DATA_DIR=~/.truthound
TRUTHOUND_AUTH_ENABLED=false
TRUTHOUND_AUTH_PASSWORD=secret
```

## Development

```bash
# Clone
git clone https://github.com/truthound/truthound-dashboard
cd truthound-dashboard

# Backend
pip install -e ".[dev]"
truthound serve --reload

# Frontend
cd frontend
npm install
npm run dev

# Tests
pytest
```

## Documentation

- [Architecture](docs/architecture.md)
- [API Reference](docs/api.md)
- [Development Guide](docs/development.md)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- [truthound](https://github.com/truthound/truthound) - Core validation engine
- [truthound-orchestration](https://github.com/truthound/truthound-orchestration) - Pipeline orchestration
```

### 3.2 API Documentation

**docs/api.md**
```markdown
# API Reference

Base URL: `http://localhost:8765/api/v1`

## Health

### GET /health

Check server status.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

## Sources

### GET /sources

List all data sources.

### POST /sources

Create a new data source.

**Request:**
```json
{
  "name": "Orders CSV",
  "type": "file",
  "config": {
    "path": "/path/to/orders.csv"
  }
}
```

### GET /sources/{id}

Get source details.

### PUT /sources/{id}

Update source.

### DELETE /sources/{id}

Delete source.

### POST /sources/{id}/test

Test connection.

## Rules

### GET /sources/{id}/schema

Get schema for a source (learned via th.learn()).

### PUT /sources/{id}/schema

Save schema configuration.

**Request:**
```json
{
  "schema_yaml": "columns:\n  order_id:\n    dtype: int64\n    nullable: false\n    unique: true",
  "validators": ["not_null", "unique", "in_range"],
  "auto_schema": true
}
```

Note: truthound uses `schema` (Schema object) and `validators` (list) instead of `rules`.

## Validations

### POST /sources/{id}/validate

Run validation.

**Request:**
```json
{
  "validators": ["not_null", "unique"],
  "schema_path": "/path/to/schema.yaml",
  "auto_schema": false
}
```

**Response:**
```json
{
  "id": "uuid",
  "source_id": "uuid",
  "status": "success",
  "passed": true,
  "has_critical": false,
  "has_high": false,
  "total_issues": 0,
  "critical_issues": 0,
  "high_issues": 0,
  "row_count": 10000,
  "column_count": 15,
  "issues": []
}
```

Note: truthound uses `validators` (list of validator names) and optional `schema` (path to YAML) instead of `rules` dict.

### GET /validations/{id}

Get validation result.

### GET /sources/{id}/validations

List validation history.

## Schedules

### GET /schedules

List all schedules.

### POST /schedules

Create schedule.

**Request:**
```json
{
  "name": "Daily Orders Check",
  "source_id": "uuid",
  "cron_expression": "0 9 * * *",
  "notify_on_failure": true
}
```

### POST /schedules/{id}/pause

Pause schedule.

### POST /schedules/{id}/resume

Resume schedule.

### POST /schedules/{id}/run

Run immediately.

### DELETE /schedules/{id}

Delete schedule.

## Notifications

### GET /notifications/channels

List channels.

### POST /notifications/channels

Create channel.

### POST /notifications/channels/{id}/test

Test channel.

### GET /notifications/rules

List rules.

### POST /notifications/rules

Create rule.

## Error Responses

All errors follow this format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message"
  }
}
```
```

---

## Task 4: CI/CD Pipeline

### 4.1 GitHub Actions - CI

**.github/workflows/ci.yml**
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install ruff black

      - name: Lint with Ruff
        run: ruff check .

      - name: Check formatting with Black
        run: black --check .

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run tests
        run: pytest --cov=truthound_dashboard --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 18

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Lint
        working-directory: frontend
        run: npm run lint

      - name: Type check
        working-directory: frontend
        run: npx tsc --noEmit

  frontend-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 18

      - name: Install and build
        working-directory: frontend
        run: |
          npm ci
          npm run build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: frontend-build
          path: src/truthound_dashboard/static/

  e2e:
    runs-on: ubuntu-latest
    needs: [frontend-build]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install backend
        run: pip install -e ".[dev]"

      - name: Download frontend build
        uses: actions/download-artifact@v4
        with:
          name: frontend-build
          path: src/truthound_dashboard/static/

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 18

      - name: Install Playwright
        working-directory: frontend
        run: |
          npm ci
          npx playwright install --with-deps chromium

      - name: Run E2E tests
        working-directory: frontend
        run: npx playwright test
```

### 4.2 Release Workflow

**.github/workflows/release.yml**
```yaml
name: Release

on:
  push:
    tags:
      - "v*"

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 18

      - name: Build frontend
        working-directory: frontend
        run: |
          npm ci
          npm run build

      - name: Build package
        run: |
          pip install build
          python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
          generate_release_notes: true
```

### 4.3 Docs Trigger

**.github/workflows/trigger-docs.yml**
```yaml
name: Trigger Docs Build

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'

jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Netlify build
        run: curl -X POST -d {} ${{ secrets.NETLIFY_BUILD_HOOK }}
```

---

## Task 5: Security

### 5.1 Connection Encryption

```python
# src/truthound_dashboard/core/encryption.py
"""Encryption utilities for sensitive data."""

from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet


def generate_key(password: str | None = None) -> bytes:
    """Generate encryption key from password or random."""
    if password:
        # Derive key from password
        key = hashlib.sha256(password.encode()).digest()
        return base64.urlsafe_b64encode(key)
    else:
        return Fernet.generate_key()


def get_fernet(key: bytes | None = None) -> Fernet:
    """Get Fernet instance for encryption/decryption."""
    if key is None:
        # Use machine-specific key
        from ..config import get_settings
        settings = get_settings()
        key_file = settings.data_dir / ".key"

        if key_file.exists():
            key = key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            os.chmod(key_file, 0o600)  # Restrict permissions

    return Fernet(key)


def encrypt_value(value: str) -> str:
    """Encrypt a string value."""
    f = get_fernet()
    return f.encrypt(value.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    """Decrypt an encrypted value."""
    f = get_fernet()
    return f.decrypt(encrypted.encode()).decode()
```

### 5.2 Secure Config Storage

```python
# src/truthound_dashboard/db/secure_config.py
"""Secure configuration storage."""

from __future__ import annotations

import json
from typing import Any

from ..core.encryption import decrypt_value, encrypt_value

# Fields that should be encrypted
SENSITIVE_FIELDS = {"password", "secret", "token", "api_key", "private_key"}


def encrypt_config(config: dict[str, Any]) -> dict[str, Any]:
    """Encrypt sensitive fields in config."""
    encrypted = {}
    for key, value in config.items():
        if any(field in key.lower() for field in SENSITIVE_FIELDS):
            if isinstance(value, str) and value:
                encrypted[key] = {"_encrypted": encrypt_value(value)}
            else:
                encrypted[key] = value
        elif isinstance(value, dict):
            encrypted[key] = encrypt_config(value)
        else:
            encrypted[key] = value
    return encrypted


def decrypt_config(config: dict[str, Any]) -> dict[str, Any]:
    """Decrypt sensitive fields in config."""
    decrypted = {}
    for key, value in config.items():
        if isinstance(value, dict):
            if "_encrypted" in value:
                decrypted[key] = decrypt_value(value["_encrypted"])
            else:
                decrypted[key] = decrypt_config(value)
        else:
            decrypted[key] = value
    return decrypted
```

### 5.3 Rate Limiting

```python
# src/truthound_dashboard/api/middleware.py
"""API middleware."""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Clean old requests
        now = time.time()
        minute_ago = now - 60
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if t > minute_ago
        ]

        # Check limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                    },
                },
            )

        # Record request
        self.requests[client_ip].append(now)

        return await call_next(request)
```

### 5.4 Security Headers

```python
# src/truthound_dashboard/api/middleware.py 추가

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
```

### 5.5 Apply Middleware

```python
# src/truthound_dashboard/main.py

from .api.middleware import RateLimitMiddleware, SecurityHeadersMiddleware

app = FastAPI(...)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=120)
```

---

## Task 6: Logging

### 6.1 Logging Configuration

```python
# src/truthound_dashboard/core/logging.py
"""Logging configuration."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from ..config import get_settings


def setup_logging(level: str = "INFO"):
    """Configure application logging."""
    settings = get_settings()

    # Create logs directory
    log_dir = settings.data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # File handler
    file_handler = logging.FileHandler(log_dir / "dashboard.log")
    file_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger("truthound_dashboard")
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Also log SQLAlchemy queries in debug mode
    if level.upper() == "DEBUG":
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

    return root_logger
```

### 6.2 Request Logging

```python
# src/truthound_dashboard/api/middleware.py 추가

import logging
import time

logger = logging.getLogger("truthound_dashboard.api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all API requests."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time

        logger.info(
            f"{request.method} {request.url.path} "
            f"- {response.status_code} "
            f"- {duration:.3f}s"
        )

        return response
```

---

## Task 7: Final Testing

### 7.1 Load Testing Script

**scripts/load_test.py**
```python
"""Simple load testing script."""

import asyncio
import time

import httpx


async def make_request(client: httpx.AsyncClient, url: str):
    """Make a single request."""
    start = time.time()
    response = await client.get(url)
    duration = time.time() - start
    return response.status_code, duration


async def run_load_test(
    base_url: str = "http://localhost:8765",
    num_requests: int = 100,
    concurrency: int = 10,
):
    """Run load test."""
    urls = [
        "/api/v1/health",
        "/api/v1/sources",
        "/api/v1/schedules",
    ]

    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(num_requests):
            url = base_url + urls[i % len(urls)]
            tasks.append(make_request(client, url))

            # Control concurrency
            if len(tasks) >= concurrency:
                results = await asyncio.gather(*tasks)
                tasks = []

                # Print stats
                success = sum(1 for r in results if r[0] == 200)
                avg_time = sum(r[1] for r in results) / len(results)
                print(f"Batch complete: {success}/{len(results)} success, avg {avg_time:.3f}s")

        # Final batch
        if tasks:
            results = await asyncio.gather(*tasks)
            success = sum(1 for r in results if r[0] == 200)
            avg_time = sum(r[1] for r in results) / len(results)
            print(f"Final batch: {success}/{len(results)} success, avg {avg_time:.3f}s")


if __name__ == "__main__":
    asyncio.run(run_load_test())
```

### 7.2 Security Checklist

```markdown
# Security Checklist

## Authentication
- [ ] Optional password protection works
- [ ] Password not logged or exposed

## Data Protection
- [ ] Sensitive config fields encrypted
- [ ] Encryption key stored securely
- [ ] Database file permissions correct

## API Security
- [ ] Rate limiting in place
- [ ] Security headers set
- [ ] CORS properly configured
- [ ] No sensitive data in error messages

## Input Validation
- [ ] All inputs validated with Pydantic
- [ ] SQL injection prevented (SQLAlchemy ORM)
- [ ] Path traversal prevented

## Dependencies
- [ ] All dependencies up to date
- [ ] No known vulnerabilities (pip-audit)
```

---

## Checklist

- [ ] Database indexes created
- [ ] Old data cleanup scheduled
- [ ] Response caching implemented
- [ ] Large dataset sampling works
- [ ] Custom exceptions defined
- [ ] Global error handler configured
- [ ] User-friendly error messages
- [ ] README.md complete
- [ ] API documentation complete
- [ ] CI workflow passing
- [ ] Release workflow configured
- [ ] Docs trigger workflow configured
- [ ] Connection encryption implemented
- [ ] Rate limiting enabled
- [ ] Security headers added
- [ ] Logging configured
- [ ] Request logging enabled
- [ ] Load tests pass
- [ ] Security checklist complete

---

## Release Preparation

### Version Bump

```bash
# Update version in pyproject.toml
# Update version in __init__.py
# Update CHANGELOG.md
```

### Pre-release Checks

```bash
# Run all tests
pytest

# Build and check package
pip install build twine
python -m build
twine check dist/*

# Test install
pip install dist/truthound_dashboard-1.0.0-py3-none-any.whl
truthound serve
```

### Tag and Release

```bash
git add .
git commit -m "Release v1.0.0"
git tag v1.0.0
git push origin main --tags
```

---

## Post-Release

1. Monitor PyPI downloads
2. Watch GitHub issues for bugs
3. Respond to community feedback
4. Plan v1.1.0 features based on user requests

---

*Congratulations! truthound-dashboard v1.0.0 is production ready!*
