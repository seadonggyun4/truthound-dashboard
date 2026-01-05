# Phase 2: Core Features (v0.2.0)

## Goal

GX Cloud 핵심 유료 기능 대응 - 검증 히스토리, 프로파일링, 자동 규칙 생성, Drift Detection, 스케줄링

## Prerequisites

- Phase 1 완료 (`truthound serve` 정상 작동)
- 기본 CRUD API 및 검증 실행 가능

---

## Task 1: Validation History

### 1.1 Database Schema Updates

**src/truthound_dashboard/db/models.py** - 기존 Validation 모델 활용

추가 인덱스 적용:
```python
from sqlalchemy import Index

# Validation 모델에 인덱스 추가
__table_args__ = (
    Index('idx_validations_source_created', 'source_id', 'created_at'),
)
```

### 1.2 History API Endpoints

**src/truthound_dashboard/api/history.py**
```python
"""Validation history API."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from ..db.database import get_db
from ..db.models import Validation

router = APIRouter()


@router.get("/sources/{source_id}/history")
async def get_validation_history(
    source_id: str,
    period: Literal["7d", "30d", "90d"] = Query("30d"),
    granularity: Literal["hourly", "daily", "weekly"] = Query("daily"),
):
    """Get validation history with trend data."""
    # Calculate date range
    days = {"7d": 7, "30d": 30, "90d": 90}[period]
    start_date = datetime.utcnow() - timedelta(days=days)

    async with get_db() as db:
        # Get validations in period
        result = await db.execute(
            select(Validation)
            .where(Validation.source_id == source_id)
            .where(Validation.created_at >= start_date)
            .order_by(Validation.created_at.desc())
        )
        validations = result.scalars().all()

        # Aggregate by granularity
        trend_data = _aggregate_by_period(validations, granularity)

        # Calculate statistics
        # Note: truthound Report uses 'passed' (bool), not 'pass_rate' (float)
        # Pass rate must be computed based on passed status
        total_runs = len(validations)
        passed_runs = sum(1 for v in validations if v.status == "success")
        failed_runs = sum(1 for v in validations if v.status == "failed")
        success_rate = (passed_runs / total_runs * 100) if total_runs > 0 else 0

        # Get failure frequency by issue type
        failure_frequency = _calculate_failure_frequency(validations)

        return {
            "success": True,
            "data": {
                "summary": {
                    "total_runs": total_runs,
                    "passed_runs": passed_runs,
                    "failed_runs": failed_runs,
                    "success_rate": round(success_rate, 2),  # Computed from passed status
                },
                "trend": trend_data,
                "failure_frequency": failure_frequency,
                "recent_validations": [
                    {
                        "id": v.id,
                        "status": v.status,
                        "passed": v.passed,
                        "has_critical": v.has_critical,
                        "has_high": v.has_high,
                        "total_issues": v.total_issues,
                        "created_at": v.created_at.isoformat(),
                    }
                    for v in validations[:10]
                ],
            },
        }


def _aggregate_by_period(validations, granularity):
    """Aggregate validations by time period."""
    from collections import defaultdict

    buckets = defaultdict(list)

    for v in validations:
        if granularity == "hourly":
            key = v.created_at.strftime("%Y-%m-%d %H:00")
        elif granularity == "daily":
            key = v.created_at.strftime("%Y-%m-%d")
        else:  # weekly
            # Get Monday of the week
            monday = v.created_at - timedelta(days=v.created_at.weekday())
            key = monday.strftime("%Y-%m-%d")

        buckets[key].append(v)

    trend = []
    for date, vals in sorted(buckets.items()):
        # truthound doesn't have pass_rate; compute from passed status
        passed_count = sum(1 for v in vals if v.passed)
        success_rate = (passed_count / len(vals) * 100) if vals else 0
        trend.append({
            "date": date,
            "success_rate": round(success_rate, 2),
            "run_count": len(vals),
            "passed_count": passed_count,
            "failed_count": len(vals) - passed_count,
        })

    return trend


def _calculate_failure_frequency(validations):
    """Calculate failure frequency by issue type.

    Note: truthound Report contains 'issues' (not 'results'), where each issue has:
    - column: str
    - issue_type: str
    - count: int
    - severity: str
    """
    from collections import Counter

    failures = Counter()

    for v in validations:
        if v.result_json and "issues" in v.result_json:
            for issue in v.result_json["issues"]:
                key = f"{issue.get('column', 'unknown')}.{issue.get('issue_type', 'unknown')}"
                failures[key] += issue.get('count', 1)

    return [
        {"issue": issue, "count": count}
        for issue, count in failures.most_common(10)
    ]
```

### 1.3 Frontend: History Page

**frontend/src/pages/History.tsx**
```tsx
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar,
} from 'recharts'

interface HistoryData {
  summary: {
    total_runs: number
    passed_runs: number
    failed_runs: number
    success_rate: number  // Computed from passed status, not from pass_rate
  }
  trend: Array<{
    date: string
    success_rate: number
    run_count: number
    passed_count: number
    failed_count: number
  }>
  failure_frequency: Array<{ issue: string; count: number }>  // 'issue', not 'rule'
  recent_validations: Array<{
    id: string
    status: string
    passed: boolean
    has_critical: boolean
    has_high: boolean
    total_issues: number
    created_at: string
  }>
}

export default function History() {
  const { id } = useParams<{ id: string }>()
  const [data, setData] = useState<HistoryData | null>(null)
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('30d')

  useEffect(() => {
    fetch(`/api/v1/sources/${id}/history?period=${period}`)
      .then(res => res.json())
      .then(res => setData(res.data))
  }, [id, period])

  if (!data) return <div>Loading...</div>

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Validation History</h1>
        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value as '7d' | '30d' | '90d')}
          className="border rounded px-3 py-2"
        >
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
          <option value="90d">Last 90 days</option>
        </select>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-500">Total Runs</div>
          <div className="text-2xl font-bold">{data.summary.total_runs}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-500">Success Rate</div>
          <div className="text-2xl font-bold text-green-600">
            {data.summary.success_rate}%
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-500">Passed</div>
          <div className="text-2xl font-bold text-green-600">
            {data.summary.passed_runs}
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-500">Failed</div>
          <div className="text-2xl font-bold text-red-600">
            {data.summary.failed_runs}
          </div>
        </div>
      </div>

      {/* Trend Chart */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Pass Rate Trend</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data.trend}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="success_rate"
              stroke="#10b981"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Failure Frequency */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Rule Failure Frequency</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data.failure_frequency} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis dataKey="issue" type="category" width={150} />
            <Tooltip />
            <Bar dataKey="count" fill="#ef4444" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Recent Validations */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Recent Validations</h2>
        <table className="w-full">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2">Time</th>
              <th className="text-left py-2">Status</th>
              <th className="text-left py-2">Result</th>
              <th className="text-left py-2">Issues</th>
            </tr>
          </thead>
          <tbody>
            {data.recent_validations.map((v) => (
              <tr key={v.id} className="border-b">
                <td className="py-2">
                  {new Date(v.created_at).toLocaleString()}
                </td>
                <td className="py-2">
                  <span className={v.status === 'success' ? 'text-green-600' : 'text-red-600'}>
                    {v.status}
                  </span>
                </td>
                <td className="py-2">
                  {v.passed ? (
                    <span className="text-green-600">Passed</span>
                  ) : (
                    <span className="text-red-600">
                      Failed
                      {v.has_critical && ' (Critical)'}
                      {v.has_high && ' (High)'}
                    </span>
                  )}
                </td>
                <td className="py-2">{v.total_issues || 0}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
```

---

## Task 2: Data Profiling

### 2.1 Profile API

**src/truthound_dashboard/api/profiles.py**
```python
"""Data profiling API."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from ..core import get_adapter
from ..db.database import get_db
from ..db.models import Profile, Source

router = APIRouter()


@router.post("/sources/{source_id}/profile")
async def run_profile(source_id: str):
    """Run data profiling on a source."""
    async with get_db() as db:
        result = await db.execute(select(Source).where(Source.id == source_id))
        source = result.scalar_one_or_none()
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

    adapter = get_adapter()
    source_path = source.config.get("path", source.config.get("connection_string"))

    try:
        profile_result = await adapter.profile(source_path)

        # Save profile
        async with get_db() as db:
            profile = Profile(
                id=str(uuid.uuid4()),
                source_id=source_id,
                profile_json=profile_result,
            )
            db.add(profile)

        return {"success": True, "data": profile_result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources/{source_id}/profile")
async def get_profile(source_id: str):
    """Get latest profile for a source."""
    async with get_db() as db:
        result = await db.execute(
            select(Profile)
            .where(Profile.source_id == source_id)
            .order_by(Profile.created_at.desc())
            .limit(1)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(status_code=404, detail="No profile found")

        return {
            "success": True,
            "data": {
                "id": profile.id,
                "source_id": profile.source_id,
                "profile": profile.profile_json,
                "created_at": profile.created_at.isoformat(),
            },
        }


@router.post("/sources/{source_id}/learn")
async def learn_schema(source_id: str, infer_constraints: bool = True):
    """Auto-generate schema from data.

    Uses truthound's th.learn() to analyze data and generate a Schema with:
    - Column types
    - Null ratios
    - Unique ratios
    - Min/max values for numeric columns
    - Allowed values for low-cardinality columns
    - Statistical summaries
    """
    async with get_db() as db:
        result = await db.execute(select(Source).where(Source.id == source_id))
        source = result.scalar_one_or_none()
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

    adapter = get_adapter()
    source_path = source.config.get("path", source.config.get("connection_string"))

    try:
        learn_result = await adapter.learn(source_path, infer_constraints=infer_constraints)
        # learn_result contains: schema, schema_yaml, row_count, column_count, columns
        return {"success": True, "data": learn_result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2.2 Profile Database Model

**src/truthound_dashboard/db/models.py** 추가:
```python
class Profile(Base):
    """Data profile model."""

    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(36), nullable=False)
    profile_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
```

### 2.3 Frontend: Profile Page

**frontend/src/pages/Profile.tsx**
```tsx
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

interface ColumnProfile {
  name: string
  dtype: string
  null_pct: string  // e.g., "5.2%"
  unique_pct: string  // e.g., "98.1%"
  min: any
  max: any
  mean: number | null
  std: number | null
}

interface ProfileData {
  source: string
  row_count: number
  column_count: number
  size_bytes: number
  columns: ColumnProfile[]
}

export default function Profile() {
  const { id } = useParams<{ id: string }>()
  const [profile, setProfile] = useState<ProfileData | null>(null)
  const [loading, setLoading] = useState(false)
  const [learnedRules, setLearnedRules] = useState<string | null>(null)

  const runProfile = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/v1/sources/${id}/profile`, { method: 'POST' })
      const data = await res.json()
      setProfile(data.data)
    } finally {
      setLoading(false)
    }
  }

  const learnRules = async () => {
    const res = await fetch(`/api/v1/sources/${id}/learn`, { method: 'POST' })
    const data = await res.json()
    // th.learn returns Schema, converted to schema_yaml in adapter
    setLearnedRules(data.data.schema_yaml)
  }

  useEffect(() => {
    fetch(`/api/v1/sources/${id}/profile`)
      .then(res => res.json())
      .then(data => {
        if (data.success) setProfile(data.data.profile)
      })
      .catch(() => {})
  }, [id])

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Data Profile</h1>
        <div className="space-x-2">
          <button
            onClick={runProfile}
            disabled={loading}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {loading ? 'Profiling...' : 'Run Profile'}
          </button>
          <button
            onClick={learnRules}
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
          >
            Generate Rules
          </button>
        </div>
      </div>

      {profile && (
        <>
          {/* Overview */}
          {/* Note: truthound ProfileReport contains: source, row_count, column_count, size_bytes, columns */}
          {/* It does NOT have 'issues' - that comes from th.check() Report */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-500">Rows</div>
              <div className="text-2xl font-bold">
                {profile.row_count.toLocaleString()}
              </div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-500">Columns</div>
              <div className="text-2xl font-bold">{profile.column_count}</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-500">Size</div>
              <div className="text-2xl font-bold">
                {(profile.size_bytes / 1024).toFixed(1)} KB
              </div>
            </div>
          </div>

          {/* Column Statistics */}
          {/* truthound ProfileReport columns have: name, dtype, null_pct (string), unique_pct (string), min, max */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left py-3 px-4">Column</th>
                  <th className="text-left py-3 px-4">Type</th>
                  <th className="text-left py-3 px-4">Nulls</th>
                  <th className="text-left py-3 px-4">Unique</th>
                  <th className="text-left py-3 px-4">Min</th>
                  <th className="text-left py-3 px-4">Max</th>
                  <th className="text-left py-3 px-4">Mean</th>
                </tr>
              </thead>
              <tbody>
                {profile.columns.map((col) => (
                  <tr key={col.name} className="border-t">
                    <td className="py-3 px-4 font-medium">{col.name}</td>
                    <td className="py-3 px-4 text-gray-500">{col.dtype}</td>
                    <td className="py-3 px-4">{col.null_pct}</td>
                    <td className="py-3 px-4">{col.unique_pct}</td>
                    <td className="py-3 px-4">{col.min ?? '-'}</td>
                    <td className="py-3 px-4">{col.max ?? '-'}</td>
                    <td className="py-3 px-4">
                      {col.mean != null ? col.mean.toFixed(2) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Learned Rules Modal */}
      {learnedRules && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-auto">
            <h2 className="text-xl font-bold mb-4">Generated Rules</h2>
            <pre className="bg-gray-100 p-4 rounded text-sm overflow-auto">
              {learnedRules}
            </pre>
            <div className="mt-4 flex justify-end space-x-2">
              <button
                onClick={() => setLearnedRules(null)}
                className="px-4 py-2 border rounded"
              >
                Close
              </button>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(learnedRules)
                }}
                className="px-4 py-2 bg-blue-500 text-white rounded"
              >
                Copy to Clipboard
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
```

---

## Task 3: Drift Detection

### 3.1 Drift API

**src/truthound_dashboard/api/drift.py**
```python
"""Drift detection API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from ..core import get_adapter
from ..db.database import get_db
from ..db.models import Source

router = APIRouter()


class DriftCompareRequest(BaseModel):
    """Drift comparison request."""

    baseline_source_id: str
    current_source_id: str
    columns: list[str] | None = None  # Columns to compare
    method: str = "auto"  # "auto", "ks", "psi", "chi2", "js"
    threshold: float | None = None
    sample_size: int | None = None  # For large datasets


@router.post("/drift/compare")
async def compare_datasets(request: DriftCompareRequest):
    """Compare two datasets for drift detection."""
    async with get_db() as db:
        # Get baseline source
        result = await db.execute(
            select(Source).where(Source.id == request.baseline_source_id)
        )
        baseline = result.scalar_one_or_none()
        if not baseline:
            raise HTTPException(status_code=404, detail="Baseline source not found")

        # Get current source
        result = await db.execute(
            select(Source).where(Source.id == request.current_source_id)
        )
        current = result.scalar_one_or_none()
        if not current:
            raise HTTPException(status_code=404, detail="Current source not found")

    adapter = get_adapter()

    baseline_path = baseline.config.get("path", baseline.config.get("connection_string"))
    current_path = current.config.get("path", current.config.get("connection_string"))

    try:
        compare_result = await adapter.compare(
            baseline_path,
            current_path,
            columns=request.columns,
            method=request.method,
            threshold=request.threshold,
            sample_size=request.sample_size,
        )

        return {
            "success": True,
            "data": {
                "id": str(uuid.uuid4()),
                "baseline": {"id": baseline.id, "name": baseline.name},
                "current": {"id": current.id, "name": current.name},
                "result": compare_result,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 3.2 Truthound Adapter - Compare Method

**src/truthound_dashboard/core/truthound_adapter.py** 추가:
```python
async def compare(
    self,
    baseline: str,
    current: str,
    columns: list[str] | None = None,
    method: str = "auto",
    threshold: float | None = None,
    sample_size: int | None = None,
) -> dict[str, Any]:
    """Compare two datasets for drift detection.

    Args:
        baseline: Reference data path.
        current: Current data path to compare.
        columns: Optional list of columns to compare. If None, all common columns.
        method: Detection method - "auto", "ks", "psi", "chi2", or "js".
        threshold: Optional custom threshold for drift detection.
        sample_size: Optional sample size for large datasets.

    Returns:
        Dictionary with drift detection results.
    """
    func = partial(
        th.compare,
        baseline,
        current,
        columns=columns,
        method=method,
        threshold=threshold,
        sample_size=sample_size,
    )

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(self._executor, func)

    return self._convert_compare_result(result)

def _convert_compare_result(self, result) -> dict[str, Any]:
    """Convert truthound DriftReport to dashboard format.

    The truthound DriftReport contains:
    - baseline_source: str
    - current_source: str
    - baseline_rows: int
    - current_rows: int
    - columns: list[ColumnDrift]
    - has_drift: bool
    - has_high_drift: bool
    - get_drifted_columns(): list[str]

    Each ColumnDrift has:
    - column: str
    - dtype: str
    - result: DriftResult (drifted, level, method, statistic, p_value)
    - baseline_stats: dict
    - current_stats: dict
    """
    return {
        "baseline_source": result.baseline_source,
        "current_source": result.current_source,
        "baseline_rows": result.baseline_rows,
        "current_rows": result.current_rows,
        "has_drift": result.has_drift,
        "has_high_drift": result.has_high_drift,
        "drifted_columns": result.get_drifted_columns(),
        "total_columns": len(result.columns),
        "columns": [
            {
                "column": col.column,
                "dtype": col.dtype,
                "drifted": col.result.drifted,
                "level": col.result.level.value,  # "high", "medium", "low", "none"
                "method": col.result.method,
                "statistic": col.result.statistic,
                "p_value": col.result.p_value,
                "baseline_stats": col.baseline_stats,
                "current_stats": col.current_stats,
            }
            for col in result.columns
        ],
    }
```

---

## Task 4: Schedule Management

### 4.1 Database Models

**src/truthound_dashboard/db/models.py** 추가:
```python
class Schedule(Base):
    """Validation schedule model."""

    __tablename__ = "schedules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_on_failure: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
```

### 4.2 Scheduler Core

**src/truthound_dashboard/core/scheduler.py**
```python
"""Validation scheduler using APScheduler."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .truthound_adapter import get_adapter
from ..db.database import get_db


class ValidationScheduler:
    """Manages scheduled validations."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._jobs: dict[str, str] = {}  # schedule_id -> job_id

    def start(self):
        """Start the scheduler."""
        self.scheduler.start()

    def shutdown(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()

    def add_schedule(
        self,
        schedule_id: str,
        source_id: str,
        cron_expression: str,
        notify_on_failure: bool = True,
    ):
        """Add a new scheduled validation."""
        trigger = CronTrigger.from_crontab(cron_expression)

        job = self.scheduler.add_job(
            self._run_validation,
            trigger=trigger,
            args=[schedule_id, source_id, notify_on_failure],
            id=f"validation_{schedule_id}",
            replace_existing=True,
        )

        self._jobs[schedule_id] = job.id

        # Calculate next run time
        next_run = trigger.get_next_fire_time(None, datetime.utcnow())
        return next_run

    def remove_schedule(self, schedule_id: str):
        """Remove a scheduled validation."""
        if schedule_id in self._jobs:
            self.scheduler.remove_job(self._jobs[schedule_id])
            del self._jobs[schedule_id]

    def pause_schedule(self, schedule_id: str):
        """Pause a schedule."""
        if schedule_id in self._jobs:
            self.scheduler.pause_job(self._jobs[schedule_id])

    def resume_schedule(self, schedule_id: str):
        """Resume a paused schedule."""
        if schedule_id in self._jobs:
            self.scheduler.resume_job(self._jobs[schedule_id])

    async def _run_validation(
        self,
        schedule_id: str,
        source_id: str,
        notify_on_failure: bool,
    ):
        """Execute scheduled validation.

        Note: truthound uses validators and schema (not rules dict).
        The dashboard stores validator configuration and optional schema path.
        """
        from ..db.models import Schedule, Source, Validation
        from sqlalchemy import select
        import uuid
        from datetime import datetime

        adapter = get_adapter()

        async with get_db() as db:
            # Get source
            result = await db.execute(
                select(Source).where(Source.id == source_id)
            )
            source = result.scalar_one_or_none()
            if not source:
                return

            # Get schema config if exists (stored in source.config)
            source_path = source.config.get("path")
            schema_path = source.config.get("schema_path")
            validators = source.config.get("validators")  # Optional validator list
            auto_schema = source.config.get("auto_schema", False)

            try:
                started_at = datetime.utcnow()
                check_result = await adapter.check(
                    data=source_path,  # th.check() uses 'data' as first param
                    validators=validators,
                    schema=schema_path,
                    auto_schema=auto_schema,
                )
                completed_at = datetime.utcnow()

                # Save validation result
                # truthound returns: passed, has_critical, has_high, total_issues, issues, etc.
                validation = Validation(
                    id=str(uuid.uuid4()),
                    source_id=source_id,
                    status="success" if check_result["passed"] else "failed",
                    passed=check_result["passed"],
                    has_critical=check_result.get("has_critical", False),
                    has_high=check_result.get("has_high", False),
                    total_issues=check_result.get("total_issues", 0),
                    row_count=check_result.get("row_count"),
                    column_count=check_result.get("column_count"),
                    result_json=check_result,
                    started_at=started_at,
                    completed_at=completed_at,
                )
                db.add(validation)

                # Update schedule last run
                result = await db.execute(
                    select(Schedule).where(Schedule.id == schedule_id)
                )
                schedule = result.scalar_one_or_none()
                if schedule:
                    schedule.last_run_at = datetime.utcnow()

                # Send notification if failed and notify_on_failure
                if notify_on_failure and not check_result["passed"]:
                    # TODO: Implement notification (Phase 3)
                    pass

            except Exception as e:
                # Log error
                print(f"Scheduled validation failed: {e}")


# Singleton
_scheduler: ValidationScheduler | None = None


def get_scheduler() -> ValidationScheduler:
    """Get singleton scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = ValidationScheduler()
    return _scheduler
```

### 4.3 Schedule API

**src/truthound_dashboard/api/schedules.py**
```python
"""Schedule management API."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from ..core.scheduler import get_scheduler
from ..db.database import get_db
from ..db.models import Schedule

router = APIRouter()


class ScheduleCreate(BaseModel):
    """Schedule creation request."""

    name: str
    source_id: str
    cron_expression: str
    notify_on_failure: bool = True


class ScheduleUpdate(BaseModel):
    """Schedule update request."""

    name: str | None = None
    cron_expression: str | None = None
    notify_on_failure: bool | None = None


@router.get("/schedules")
async def list_schedules():
    """List all schedules."""
    async with get_db() as db:
        result = await db.execute(
            select(Schedule).order_by(Schedule.created_at.desc())
        )
        schedules = result.scalars().all()

        return {
            "success": True,
            "data": [
                {
                    "id": s.id,
                    "name": s.name,
                    "source_id": s.source_id,
                    "cron_expression": s.cron_expression,
                    "is_active": s.is_active,
                    "notify_on_failure": s.notify_on_failure,
                    "last_run_at": s.last_run_at.isoformat() if s.last_run_at else None,
                    "next_run_at": s.next_run_at.isoformat() if s.next_run_at else None,
                    "created_at": s.created_at.isoformat(),
                }
                for s in schedules
            ],
        }


@router.post("/schedules")
async def create_schedule(request: ScheduleCreate):
    """Create a new schedule."""
    scheduler = get_scheduler()

    schedule_id = str(uuid.uuid4())

    # Add to APScheduler
    next_run = scheduler.add_schedule(
        schedule_id=schedule_id,
        source_id=request.source_id,
        cron_expression=request.cron_expression,
        notify_on_failure=request.notify_on_failure,
    )

    # Save to database
    async with get_db() as db:
        schedule = Schedule(
            id=schedule_id,
            name=request.name,
            source_id=request.source_id,
            cron_expression=request.cron_expression,
            is_active=True,
            notify_on_failure=request.notify_on_failure,
            next_run_at=next_run,
        )
        db.add(schedule)

    return {
        "success": True,
        "data": {
            "id": schedule_id,
            "name": request.name,
            "next_run_at": next_run.isoformat() if next_run else None,
        },
    }


@router.post("/schedules/{schedule_id}/pause")
async def pause_schedule(schedule_id: str):
    """Pause a schedule."""
    scheduler = get_scheduler()
    scheduler.pause_schedule(schedule_id)

    async with get_db() as db:
        result = await db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        if schedule:
            schedule.is_active = False

    return {"success": True}


@router.post("/schedules/{schedule_id}/resume")
async def resume_schedule(schedule_id: str):
    """Resume a paused schedule."""
    scheduler = get_scheduler()
    scheduler.resume_schedule(schedule_id)

    async with get_db() as db:
        result = await db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        if schedule:
            schedule.is_active = True

    return {"success": True}


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    """Delete a schedule."""
    scheduler = get_scheduler()
    scheduler.remove_schedule(schedule_id)

    async with get_db() as db:
        result = await db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        if schedule:
            await db.delete(schedule)

    return {"success": True}


@router.post("/schedules/{schedule_id}/run")
async def run_schedule_now(schedule_id: str):
    """Run a schedule immediately."""
    async with get_db() as db:
        result = await db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

    scheduler = get_scheduler()
    await scheduler._run_validation(
        schedule_id,
        schedule.source_id,
        schedule.notify_on_failure,
    )

    return {"success": True, "message": "Validation triggered"}
```

### 4.4 Update Main App

**src/truthound_dashboard/main.py** 수정:
```python
from .core.scheduler import get_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_db()

    # Start scheduler
    scheduler = get_scheduler()
    scheduler.start()

    # Load existing schedules from DB
    await _load_schedules(scheduler)

    yield

    # Shutdown
    scheduler.shutdown()


async def _load_schedules(scheduler):
    """Load existing schedules from database."""
    from sqlalchemy import select
    from .db.models import Schedule

    async with get_db() as db:
        result = await db.execute(
            select(Schedule).where(Schedule.is_active == True)
        )
        schedules = result.scalars().all()

        for s in schedules:
            scheduler.add_schedule(
                schedule_id=s.id,
                source_id=s.source_id,
                cron_expression=s.cron_expression,
                notify_on_failure=s.notify_on_failure,
            )
```

---

## Task 5: Multi-Database Support

### 5.1 Connection Factory

**src/truthound_dashboard/core/connections.py**
```python
"""Database connection factory."""

from __future__ import annotations

from typing import Any


def build_connection_string(source_type: str, config: dict[str, Any]) -> str:
    """Build connection string from source configuration."""
    if source_type == "file":
        return config["path"]

    elif source_type == "postgresql":
        return (
            f"postgresql://{config['username']}:{config['password']}"
            f"@{config['host']}:{config.get('port', 5432)}"
            f"/{config['database']}"
        )

    elif source_type == "mysql":
        return (
            f"mysql://{config['username']}:{config['password']}"
            f"@{config['host']}:{config.get('port', 3306)}"
            f"/{config['database']}"
        )

    elif source_type == "snowflake":
        return (
            f"snowflake://{config['username']}:{config['password']}"
            f"@{config['account']}/{config['database']}"
            f"/{config.get('schema', 'PUBLIC')}"
            f"?warehouse={config['warehouse']}"
        )

    elif source_type == "bigquery":
        return f"bigquery://{config['project']}/{config.get('dataset', '')}"

    else:
        raise ValueError(f"Unknown source type: {source_type}")


async def test_connection(source_type: str, config: dict[str, Any]) -> dict:
    """Test database connection."""
    try:
        connection_string = build_connection_string(source_type, config)

        if source_type == "file":
            from pathlib import Path
            path = Path(config["path"])
            if not path.exists():
                return {"success": False, "error": "File not found"}
            return {"success": True, "message": f"File exists: {path.name}"}

        # For databases, use truthound to test
        import truthound as th
        # Simple query to test connection
        result = th.profile(connection_string)
        return {
            "success": True,
            "message": f"Connected! Found {result.column_count} columns",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 5.2 Connection Test API

**src/truthound_dashboard/api/sources.py** 추가:
```python
from ..core.connections import test_connection

@router.post("/{source_id}/test")
async def test_source_connection(source_id: str):
    """Test connection to a data source."""
    async with get_db() as db:
        result = await db.execute(select(Source).where(Source.id == source_id))
        source = result.scalar_one_or_none()
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

    test_result = await test_connection(source.type, source.config)
    return {"success": True, "data": test_result}
```

---

## Task 6: Update API Router

**src/truthound_dashboard/api/router.py** 수정:
```python
"""API router configuration."""

from fastapi import APIRouter

from . import drift, health, history, profiles, rules, schedules, sources, validations

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(rules.router, tags=["rules"])
api_router.include_router(validations.router, tags=["validations"])
api_router.include_router(history.router, tags=["history"])
api_router.include_router(profiles.router, tags=["profiles"])
api_router.include_router(drift.router, tags=["drift"])
api_router.include_router(schedules.router, tags=["schedules"])
```

---

## pyproject.toml Updates

```toml
dependencies = [
    # ... existing ...
    "apscheduler>=3.10.0",
    "pyyaml>=6.0.0",
]
```

---

## Checklist

- [ ] Validation history API implemented
- [ ] Trend chart working in frontend
- [ ] Failure frequency analysis working
- [ ] Data profiling API implemented
- [ ] Profile page showing statistics
- [ ] Auto rule generation (th.learn) working
- [ ] Drift detection API implemented
- [ ] Drift comparison UI working
- [ ] APScheduler integrated
- [ ] Schedule CRUD API working
- [ ] Schedules UI page working
- [ ] Multi-database connections supported
- [ ] Connection testing working
- [ ] All tests passing

---

## Next Steps

Phase 2 완료 후 [Phase 3: Notifications & Polish](./phase-3-notifications.md)로 진행합니다.
