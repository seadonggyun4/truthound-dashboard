# Phase 1: Foundation (v0.1.0)

## Goal

핵심 기능 MVP - `pip install truthound-dashboard && truthound serve` 실행 시 즉시 사용 가능한 대시보드

## Prerequisites

```bash
# Python 3.11+
python --version

# Node.js 18+ (Frontend 개발용)
node --version
```

---

## Task 1: Project Setup

### 1.1 Repository Structure

```bash
mkdir truthound-dashboard && cd truthound-dashboard

# 디렉토리 구조 생성
mkdir -p src/truthound_dashboard/{api,core,db,schemas,static}
mkdir -p frontend/src/{pages,components,hooks,api,lib}
mkdir -p tests/{test_api,test_core,test_db}
mkdir -p .github/workflows
```

### 1.2 pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "truthound-dashboard"
version = "0.1.0"
description = "Open-source data quality dashboard - GX Cloud alternative"
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
authors = [{ name = "Your Name", email = "your@email.com" }]
keywords = ["data-quality", "dashboard", "truthound", "validation"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Framework :: FastAPI",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "truthound>=1.0.5",
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "aiosqlite>=0.19.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.26.0",
    "ruff>=0.1.0",
    "black>=23.0.0",
]

[project.scripts]
truthound-dashboard = "truthound_dashboard.cli:app"

[project.entry-points."truthound.cli"]
serve = "truthound_dashboard.cli:register_commands"

[tool.hatch.build.targets.wheel]
packages = ["src/truthound_dashboard"]

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### 1.3 Initial Files

**src/truthound_dashboard/__init__.py**
```python
"""Truthound Dashboard - Open-source data quality dashboard."""

__version__ = "0.1.0"
```

**src/truthound_dashboard/__main__.py**
```python
"""Allow running as python -m truthound_dashboard."""

from .cli import app

if __name__ == "__main__":
    app()
```

---

## Task 2: CLI Entry Point (CRITICAL)

### 2.1 src/truthound_dashboard/cli.py

```python
"""CLI entry point for truthound-dashboard."""

from __future__ import annotations

import webbrowser
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(
    name="truthound-dashboard",
    help="Open-source data quality dashboard",
)
console = Console()


@app.command()
def serve(
    port: int = typer.Option(8765, "--port", "-p", help="Port to run on"),
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind"),
    data_dir: str = typer.Option(
        None, "--data-dir", "-d", help="Data directory path"
    ),
    no_browser: bool = typer.Option(
        False, "--no-browser", help="Don't open browser automatically"
    ),
    reload: bool = typer.Option(
        False, "--reload", help="Enable hot reload for development"
    ),
):
    """Start the truthound dashboard server."""
    import uvicorn

    from .config import get_settings

    settings = get_settings()

    # Override data directory if specified
    if data_dir:
        settings.data_dir = Path(data_dir).expanduser()

    # Ensure data directory exists
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[green]✓[/green] Database: {settings.database_path}")

    url = f"http://{host}:{port}"
    console.print(f"[green]✓[/green] Dashboard running at {url}")

    # Open browser
    if not no_browser:
        webbrowser.open(url)
        console.print("[green]✓[/green] Opening browser...")

    # Run server
    uvicorn.run(
        "truthound_dashboard.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="warning",
    )


def register_commands(typer_app: typer.Typer) -> None:
    """Register serve command with truthound CLI.

    This function is called by truthound CLI plugin system.
    """
    @typer_app.command(name="serve")
    def serve_dashboard(
        port: int = typer.Option(8765, "--port", "-p", help="Port to run on"),
        host: str = typer.Option("127.0.0.1", "--host", help="Host to bind"),
        data_dir: str = typer.Option(
            None, "--data-dir", "-d", help="Data directory path"
        ),
        no_browser: bool = typer.Option(
            False, "--no-browser", help="Don't open browser automatically"
        ),
        reload: bool = typer.Option(
            False, "--reload", help="Enable hot reload for development"
        ),
    ):
        """Start the truthound dashboard server."""
        serve(port=port, host=host, data_dir=data_dir, no_browser=no_browser, reload=reload)


if __name__ == "__main__":
    app()
```

### 2.2 src/truthound_dashboard/config.py

```python
"""Configuration settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Dashboard configuration settings."""

    # Data storage
    data_dir: Path = Path.home() / ".truthound"

    # Server
    host: str = "127.0.0.1"
    port: int = 8765

    # Optional authentication
    auth_enabled: bool = False
    auth_password: str | None = None

    # Validation defaults
    sample_size: int = 10000
    max_failed_rows: int = 1000
    default_timeout: int = 300

    @property
    def database_path(self) -> Path:
        """Get database file path."""
        return self.data_dir / "dashboard.db"

    class Config:
        env_prefix = "TRUTHOUND_"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

---

## Task 3: Database Setup (CRITICAL)

### 3.1 src/truthound_dashboard/db/database.py

```python
"""Database connection and initialization."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..config import get_settings

_engine = None
_session_factory = None


def get_engine():
    """Get or create database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        _engine = create_async_engine(
            f"sqlite+aiosqlite:///{settings.database_path}",
            echo=False,
        )
    return _engine


def get_session_factory():
    """Get or create session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session context manager."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Initialize database tables."""
    from .models import Base

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

### 3.2 src/truthound_dashboard/db/models.py

```python
"""SQLAlchemy database models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Source(Base):
    """Data source model."""

    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Schema(Base):
    """Learned schema model for validation.

    Stores truthound Schema objects (from th.learn) which contain:
    - columns: dict[str, ColumnSchema] with dtype, nullable, unique, constraints
    - row_count: int
    - version: str

    The schema_yaml field stores the YAML representation for display/editing.
    """

    __tablename__ = "schemas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(36), nullable=False)
    schema_yaml: Mapped[str] = mapped_column(Text, nullable=False)
    schema_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Validation(Base):
    """Validation result model.

    Stores truthound validation results which contain:
    - passed: bool - whether validation passed (no issues found)
    - has_critical: bool - whether any critical severity issues exist
    - has_high: bool - whether any high severity issues exist
    - total_issues: int - total number of issues found
    - issues: list - list of validation issues with column, issue_type, count, severity
    - row_count: int - number of rows in the data
    - column_count: int - number of columns in the data
    """

    __tablename__ = "validations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # "running", "success", "failed", "error"
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_critical: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_high: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    total_issues: Mapped[int | None] = mapped_column(Integer, nullable=True)
    critical_issues: Mapped[int | None] = mapped_column(Integer, nullable=True)
    high_issues: Mapped[int | None] = mapped_column(Integer, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )


class Settings(Base):
    """Application settings model."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
```

### 3.3 src/truthound_dashboard/db/__init__.py

```python
"""Database module."""

from .database import get_db, init_db
from .models import Base, Schema, Settings, Source, Validation

__all__ = [
    "get_db",
    "init_db",
    "Base",
    "Source",
    "Schema",
    "Validation",
    "Settings",
]
```

---

## Task 4: Truthound Adapter (CRITICAL)

### 4.1 src/truthound_dashboard/core/truthound_adapter.py

```python
"""Wrapper for truthound package."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any

import truthound as th


class TruthoundAdapter:
    """Async wrapper for truthound functions."""

    def __init__(self, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    async def check(
        self,
        data: str,
        validators: list[str] | None = None,
        schema: str | None = None,
        auto_schema: bool = False,
        parallel: bool = False,
    ) -> dict[str, Any]:
        """Run data validation.

        Args:
            data: Data source path (CSV, Parquet, etc.) or DataFrame.
                 Note: th.check() uses 'data' as first param, 'source' is for DataSource.
            validators: Optional list of validator names to run.
                       If None, all built-in validators are used.
            schema: Optional path to schema YAML file for schema validation.
            auto_schema: If True, auto-learns and caches schema for validation.
            parallel: If True, uses DAG-based parallel execution (default: False).

        Returns:
            Dictionary with validation results.
        """
        func = partial(
            th.check,
            data,  # First positional param is 'data', not 'source'
            validators=validators,
            schema=schema,
            auto_schema=auto_schema,
            parallel=parallel,
        )

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, func)

        return self._convert_check_result(result)

    async def profile(self, source: str) -> dict[str, Any]:
        """Run data profiling."""
        func = partial(th.profile, source)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, func)

        return self._convert_profile_result(result)

    async def learn(
        self, source: str, infer_constraints: bool = True
    ) -> dict[str, Any]:
        """Learn schema from data.

        Uses truthound's th.learn() to analyze data and generate a Schema with:
        - Column types, nullable/unique constraints
        - Min/max values, allowed values for low-cardinality columns
        - Statistical summaries (mean, std, quantiles)

        Args:
            source: Data source path.
            infer_constraints: If True, infer constraints from data statistics.

        Returns:
            Dictionary with schema, schema_yaml, row_count, column_count, columns.
        """
        func = partial(th.learn, source, infer_constraints=infer_constraints)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, func)

        return self._convert_learn_result(result)

    def _convert_check_result(self, result) -> dict[str, Any]:
        """Convert truthound Report to dashboard format.

        The truthound Report contains:
        - issues: list[ValidationIssue] - Each issue has:
            - column: str
            - issue_type: str
            - count: int
            - severity: Severity
            - details: str | None  (NOT 'message')
            - expected: Any | None
            - actual: Any | None
            - sample_values: list[Any] | None
        - source: str
        - row_count: int
        - column_count: int
        - has_issues: bool
        - has_critical: bool
        - has_high: bool
        """
        total_issues = len(result.issues)
        critical_count = sum(1 for i in result.issues if i.severity.value == "critical")
        high_count = sum(1 for i in result.issues if i.severity.value == "high")

        return {
            "passed": not result.has_issues,
            "has_critical": result.has_critical,
            "has_high": result.has_high,
            "total_issues": total_issues,
            "critical_issues": critical_count,
            "high_issues": high_count,
            "source": result.source,
            "row_count": result.row_count,
            "column_count": result.column_count,
            "issues": [
                {
                    "column": issue.column,
                    "issue_type": issue.issue_type,
                    "count": issue.count,
                    "severity": issue.severity.value,
                    "details": issue.details,  # Note: ValidationIssue has 'details', not 'message'
                    "expected": issue.expected,
                    "actual": issue.actual,
                }
                for issue in result.issues
            ],
        }

    def _convert_profile_result(self, result) -> dict[str, Any]:
        """Convert truthound ProfileReport to dashboard format.

        The truthound ProfileReport contains:
        - source: str
        - row_count: int
        - column_count: int
        - size_bytes: int
        - columns: list[dict] - Each dict has name, dtype, null_pct, unique_pct, min, max
        """
        return {
            "source": result.source,
            "row_count": result.row_count,
            "column_count": result.column_count,
            "size_bytes": result.size_bytes,
            "columns": [
                {
                    "name": col["name"],
                    "dtype": col["dtype"],
                    "null_pct": col.get("null_pct", "0%"),
                    "unique_pct": col.get("unique_pct", "0%"),
                    "min": col.get("min"),
                    "max": col.get("max"),
                    "mean": col.get("mean"),
                    "std": col.get("std"),
                }
                for col in result.columns
            ],
        }

    def _convert_learn_result(self, result) -> dict[str, Any]:
        """Convert truthound Schema to dashboard format.

        The truthound th.learn() returns a Schema object with:
        - columns: dict[str, ColumnSchema] - column name -> column schema
        - row_count: int | None
        - version: str
        - to_dict(): Convert schema to dictionary
        - save(path): Save schema to YAML file

        Each ColumnSchema has:
        - name, dtype, nullable, unique
        - min_value, max_value, allowed_values, pattern, min_length, max_length
        - null_ratio, unique_ratio, mean, std, quantiles
        """
        schema_dict = result.to_dict()
        # Convert to YAML string for display/editing
        import yaml
        schema_yaml = yaml.dump(schema_dict, default_flow_style=False, sort_keys=False)

        return {
            "schema": schema_dict,
            "schema_yaml": schema_yaml,
            "row_count": result.row_count,
            "column_count": len(result.columns),
            "columns": list(result.columns.keys()),
        }


# Singleton
_adapter: TruthoundAdapter | None = None


def get_adapter() -> TruthoundAdapter:
    """Get singleton adapter instance."""
    global _adapter
    if _adapter is None:
        _adapter = TruthoundAdapter()
    return _adapter
```

### 4.2 src/truthound_dashboard/core/__init__.py

```python
"""Core module."""

from .truthound_adapter import TruthoundAdapter, get_adapter

__all__ = ["TruthoundAdapter", "get_adapter"]
```

---

## Task 5: FastAPI Application (CRITICAL)

### 5.1 src/truthound_dashboard/main.py

```python
"""FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.router import api_router
from .db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_db()
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title="truthound-dashboard",
    description="Open-source data quality dashboard",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix="/api/v1")

# Static files (React SPA)
static_dir = Path(__file__).parent / "static"
if static_dir.exists() and (static_dir / "index.html").exists():
    # Serve static assets
    if (static_dir / "assets").exists():
        app.mount(
            "/assets",
            StaticFiles(directory=static_dir / "assets"),
            name="assets",
        )

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA fallback - serve index.html for all routes."""
        file_path = static_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(static_dir / "index.html")
```

### 5.2 src/truthound_dashboard/api/router.py

```python
"""API router configuration."""

from fastapi import APIRouter

from . import health, schemas, sources, validations

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(schemas.router, tags=["schemas"])
api_router.include_router(
    validations.router, prefix="/validations", tags=["validations"]
)
```

### 5.3 src/truthound_dashboard/api/health.py

```python
"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Check server health."""
    return {"status": "ok", "version": "0.1.0"}
```

---

## Task 6: Pydantic Schemas

### 6.1 src/truthound_dashboard/schemas/source.py

```python
"""Source schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SourceBase(BaseModel):
    """Base source schema."""

    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., pattern="^(file|postgresql|mysql|snowflake|bigquery)$")
    config: dict[str, Any]


class SourceCreate(SourceBase):
    """Schema for creating a source."""

    pass


class SourceUpdate(BaseModel):
    """Schema for updating a source."""

    name: str | None = Field(None, min_length=1, max_length=255)
    config: dict[str, Any] | None = None


class SourceResponse(SourceBase):
    """Schema for source response."""

    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SourceListResponse(BaseModel):
    """Schema for source list response."""

    success: bool = True
    data: list[SourceResponse]
```

### 6.2 src/truthound_dashboard/schemas/validation.py

```python
"""Validation schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any  # Used for expected/actual fields

from pydantic import BaseModel


class ValidationIssue(BaseModel):
    """Single validation issue found.

    Maps to truthound's ValidationIssue dataclass which has:
    - column: str
    - issue_type: str
    - count: int
    - severity: Severity
    - details: str | None  (not 'message')
    - expected: Any | None
    - actual: Any | None
    - sample_values: list[Any] | None
    """

    column: str
    issue_type: str
    count: int
    severity: str  # "critical", "high", "medium", "low"
    details: str | None = None  # Note: truthound uses 'details', not 'message'
    expected: Any | None = None
    actual: Any | None = None


class ValidationResponse(BaseModel):
    """Validation response schema."""

    id: str
    source_id: str
    status: str  # "running", "success", "failed", "error"
    passed: bool | None = None
    has_critical: bool | None = None
    has_high: bool | None = None
    total_issues: int | None = None
    critical_issues: int | None = None
    high_issues: int | None = None
    row_count: int | None = None
    column_count: int | None = None
    issues: list[ValidationIssue] = []
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ValidationRunRequest(BaseModel):
    """Request to run validation."""

    validators: list[str] | None = None  # List of validator names, e.g. ["null", "duplicate"]
    schema_path: str | None = None  # Path to schema YAML file
    auto_schema: bool = False  # Auto-learn and cache schema
```

### 6.3 src/truthound_dashboard/schemas/__init__.py

```python
"""Pydantic schemas."""

from .source import (
    SourceBase,
    SourceCreate,
    SourceListResponse,
    SourceResponse,
    SourceUpdate,
)
from .validation import ValidationIssue, ValidationResponse, ValidationRunRequest

__all__ = [
    "SourceBase",
    "SourceCreate",
    "SourceUpdate",
    "SourceResponse",
    "SourceListResponse",
    "ValidationIssue",
    "ValidationResponse",
    "ValidationRunRequest",
]
```

---

## Task 7: API Endpoints

### 7.1 src/truthound_dashboard/api/sources.py

```python
"""Sources API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from ..db.database import get_db
from ..db.models import Source
from ..schemas import SourceCreate, SourceListResponse, SourceResponse, SourceUpdate

router = APIRouter()


@router.get("", response_model=SourceListResponse)
async def list_sources():
    """List all data sources."""
    async with get_db() as db:
        result = await db.execute(select(Source).order_by(Source.created_at.desc()))
        sources = result.scalars().all()
        return SourceListResponse(
            data=[SourceResponse.model_validate(s) for s in sources]
        )


@router.post("", response_model=SourceResponse)
async def create_source(source: SourceCreate):
    """Create a new data source."""
    async with get_db() as db:
        db_source = Source(
            id=str(uuid.uuid4()),
            name=source.name,
            type=source.type,
            config=source.config,
        )
        db.add(db_source)
        await db.flush()
        await db.refresh(db_source)
        return SourceResponse.model_validate(db_source)


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(source_id: str):
    """Get a specific data source."""
    async with get_db() as db:
        result = await db.execute(select(Source).where(Source.id == source_id))
        source = result.scalar_one_or_none()
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        return SourceResponse.model_validate(source)


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(source_id: str, update: SourceUpdate):
    """Update a data source."""
    async with get_db() as db:
        result = await db.execute(select(Source).where(Source.id == source_id))
        source = result.scalar_one_or_none()
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        if update.name is not None:
            source.name = update.name
        if update.config is not None:
            source.config = update.config
        source.updated_at = datetime.utcnow()

        await db.flush()
        await db.refresh(source)
        return SourceResponse.model_validate(source)


@router.delete("/{source_id}")
async def delete_source(source_id: str):
    """Delete a data source."""
    async with get_db() as db:
        result = await db.execute(select(Source).where(Source.id == source_id))
        source = result.scalar_one_or_none()
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        await db.delete(source)
        return {"success": True, "message": "Source deleted"}
```

### 7.2 src/truthound_dashboard/api/validations.py

```python
"""Validations API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from ..core import get_adapter
from ..db.database import get_db
from ..db.models import Source, Validation
from ..schemas import ValidationResponse, ValidationRunRequest

router = APIRouter()


@router.post("/sources/{source_id}/validate", response_model=ValidationResponse)
async def run_validation(source_id: str, request: ValidationRunRequest):
    """Run validation on a data source."""
    async with get_db() as db:
        # Get source
        result = await db.execute(select(Source).where(Source.id == source_id))
        source = result.scalar_one_or_none()
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        # Create validation record
        validation_id = str(uuid.uuid4())
        validation = Validation(
            id=validation_id,
            source_id=source_id,
            status="running",
            started_at=datetime.utcnow(),
        )
        db.add(validation)
        await db.flush()

    # Run validation
    adapter = get_adapter()
    try:
        # Get source path from config
        source_path = source.config.get("path", source.config.get("connection_string"))

        # Note: th.check() uses 'data' as first positional param, not 'source'
        # 'source' is for DataSource objects
        check_result = await adapter.check(
            data=source_path,
            validators=request.validators,
            schema=request.schema_path,
            auto_schema=request.auto_schema,
        )

        # Update validation record
        async with get_db() as db:
            result = await db.execute(
                select(Validation).where(Validation.id == validation_id)
            )
            validation = result.scalar_one()

            # truthound Report has: has_issues, has_critical, has_high, issues
            validation.status = "success" if check_result["passed"] else "failed"
            validation.passed = check_result["passed"]
            validation.has_critical = check_result.get("has_critical", False)
            validation.has_high = check_result.get("has_high", False)
            validation.total_issues = check_result.get("total_issues", 0)
            validation.critical_issues = check_result.get("critical_issues", 0)
            validation.high_issues = check_result.get("high_issues", 0)
            validation.row_count = check_result.get("row_count")
            validation.column_count = check_result.get("column_count")
            validation.result_json = check_result
            validation.completed_at = datetime.utcnow()

            await db.flush()
            await db.refresh(validation)

            return ValidationResponse(
                id=validation.id,
                source_id=validation.source_id,
                status=validation.status,
                passed=validation.passed,
                has_critical=validation.has_critical,
                has_high=validation.has_high,
                total_issues=validation.total_issues,
                critical_issues=validation.critical_issues,
                high_issues=validation.high_issues,
                row_count=validation.row_count,
                column_count=validation.column_count,
                issues=check_result.get("issues", []),
                created_at=validation.created_at,
            )

    except Exception as e:
        # Update validation as error
        async with get_db() as db:
            result = await db.execute(
                select(Validation).where(Validation.id == validation_id)
            )
            validation = result.scalar_one()
            validation.status = "error"
            validation.completed_at = datetime.utcnow()
            validation.result_json = {"error": str(e)}

        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{validation_id}", response_model=ValidationResponse)
async def get_validation(validation_id: str):
    """Get validation result."""
    async with get_db() as db:
        result = await db.execute(
            select(Validation).where(Validation.id == validation_id)
        )
        validation = result.scalar_one_or_none()
        if not validation:
            raise HTTPException(status_code=404, detail="Validation not found")

        return ValidationResponse(
            id=validation.id,
            source_id=validation.source_id,
            status=validation.status,
            passed=validation.passed,
            has_critical=validation.has_critical,
            has_high=validation.has_high,
            total_issues=validation.total_issues,
            critical_issues=validation.critical_issues,
            high_issues=validation.high_issues,
            row_count=validation.row_count,
            column_count=validation.column_count,
            issues=validation.result_json.get("issues", []) if validation.result_json else [],
            started_at=validation.started_at,
            completed_at=validation.completed_at,
            created_at=validation.created_at,
        )


@router.get("/sources/{source_id}/validations")
async def list_source_validations(source_id: str, limit: int = 20):
    """List validations for a source."""
    async with get_db() as db:
        result = await db.execute(
            select(Validation)
            .where(Validation.source_id == source_id)
            .order_by(Validation.created_at.desc())
            .limit(limit)
        )
        validations = result.scalars().all()
        return {
            "success": True,
            "data": [
                ValidationResponse(
                    id=v.id,
                    source_id=v.source_id,
                    status=v.status,
                    passed=v.passed,
                    has_critical=v.has_critical,
                    has_high=v.has_high,
                    total_issues=v.total_issues,
                    critical_issues=v.critical_issues,
                    high_issues=v.high_issues,
                    row_count=v.row_count,
                    column_count=v.column_count,
                    issues=[],  # List endpoint doesn't include full issues
                    started_at=v.started_at,
                    completed_at=v.completed_at,
                    created_at=v.created_at,
                )
                for v in validations
            ],
        }
```

### 7.3 src/truthound_dashboard/api/rules.py

```python
"""Rules API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from ..db.database import get_db
from ..db.models import Rule, Source

router = APIRouter()


class RulesUpdate(BaseModel):
    """Rules update request."""

    rules_yaml: str


class RulesResponse(BaseModel):
    """Rules response."""

    id: str
    source_id: str
    rules_yaml: str


@router.get("/sources/{source_id}/rules", response_model=RulesResponse | None)
async def get_rules(source_id: str):
    """Get rules for a source."""
    async with get_db() as db:
        # Verify source exists
        source_result = await db.execute(
            select(Source).where(Source.id == source_id)
        )
        if not source_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Source not found")

        result = await db.execute(
            select(Rule).where(Rule.source_id == source_id)
        )
        rule = result.scalar_one_or_none()

        if not rule:
            return None

        return RulesResponse(
            id=rule.id,
            source_id=rule.source_id,
            rules_yaml=rule.rules_yaml,
        )


@router.put("/sources/{source_id}/rules", response_model=RulesResponse)
async def update_rules(source_id: str, update: RulesUpdate):
    """Create or update rules for a source."""
    async with get_db() as db:
        # Verify source exists
        source_result = await db.execute(
            select(Source).where(Source.id == source_id)
        )
        if not source_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Source not found")

        result = await db.execute(
            select(Rule).where(Rule.source_id == source_id)
        )
        rule = result.scalar_one_or_none()

        if rule:
            rule.rules_yaml = update.rules_yaml
        else:
            rule = Rule(
                id=str(uuid.uuid4()),
                source_id=source_id,
                rules_yaml=update.rules_yaml,
            )
            db.add(rule)

        await db.flush()
        await db.refresh(rule)

        return RulesResponse(
            id=rule.id,
            source_id=rule.source_id,
            rules_yaml=rule.rules_yaml,
        )
```

### 7.4 src/truthound_dashboard/api/__init__.py

```python
"""API module."""

from . import health, rules, sources, validations

__all__ = ["health", "sources", "rules", "validations"]
```

---

## Task 8: React Frontend Setup (CRITICAL)

### 8.1 frontend/package.json

```json
{
  "name": "truthound-dashboard-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-label": "^2.0.2",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-toast": "^1.1.5",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "lucide-react": "^0.312.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.3",
    "recharts": "^2.10.4",
    "tailwind-merge": "^2.2.1",
    "tailwindcss-animate": "^1.0.7",
    "zustand": "^4.5.0"
  },
  "devDependencies": {
    "@types/node": "^20.11.5",
    "@types/react": "^18.2.48",
    "@types/react-dom": "^18.2.18",
    "@typescript-eslint/eslint-plugin": "^6.19.1",
    "@typescript-eslint/parser": "^6.19.1",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.17",
    "eslint": "^8.56.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.33",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.12"
  }
}
```

### 8.2 frontend/vite.config.ts

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../src/truthound_dashboard/static',
    emptyOutDir: true,
  },
})
```

### 8.3 frontend/src/main.tsx

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
```

### 8.4 frontend/src/App.tsx

```tsx
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Sources from './pages/Sources'
import Rules from './pages/Rules'
import Validations from './pages/Validations'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="sources" element={<Sources />} />
        <Route path="sources/:id/rules" element={<Rules />} />
        <Route path="validations/:id" element={<Validations />} />
      </Route>
    </Routes>
  )
}

export default App
```

---

## Task 9: Tests

### 9.1 tests/conftest.py

```python
"""Test fixtures."""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from truthound_dashboard.db.models import Base
from truthound_dashboard.main import app


@pytest_asyncio.fixture
async def async_client():
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def db_session():
    """Create in-memory database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()
```

### 9.2 tests/test_api/test_health.py

```python
"""Health endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_health_check(async_client):
    """Test health endpoint returns ok."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
```

### 9.3 tests/test_api/test_sources.py

```python
"""Sources API tests."""

import pytest


@pytest.mark.asyncio
async def test_list_sources_empty(async_client):
    """Test listing sources when empty."""
    response = await async_client.get("/api/v1/sources")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] == []


@pytest.mark.asyncio
async def test_create_source(async_client):
    """Test creating a source."""
    response = await async_client.post(
        "/api/v1/sources",
        json={
            "name": "Test CSV",
            "type": "file",
            "config": {"path": "/path/to/test.csv"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test CSV"
    assert data["type"] == "file"
    assert "id" in data
```

---

## Task 10: PyPI Package Setup

### 10.1 Build & Test

```bash
# Install in dev mode
pip install -e ".[dev]"

# Run tests
pytest

# Build package
pip install build
python -m build

# Check package
pip install twine
twine check dist/*
```

### 10.2 GitHub Actions CI

**.github/workflows/ci.yml**
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
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
        run: |
          pip install -e ".[dev]"

      - name: Lint with ruff
        run: ruff check .

      - name: Test with pytest
        run: pytest --cov=truthound_dashboard

  build-frontend:
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
          npm install
          npm run build
```

---

## Checklist

- [ ] Project structure created
- [ ] pyproject.toml configured
- [ ] CLI (`truthound serve`) working
- [ ] Config module working
- [ ] Database models created
- [ ] Database initialization working
- [ ] Truthound adapter implemented
- [ ] FastAPI app running
- [ ] Health endpoint working
- [ ] Sources CRUD API working
- [ ] Rules API working
- [ ] Validations API working
- [ ] React SPA basic structure
- [ ] Frontend builds to static/
- [ ] Tests passing
- [ ] CI workflow working

---

## Next Steps

Phase 1 완료 후 [Phase 2: Core Features](./phase-2-core-features.md)로 진행합니다.
