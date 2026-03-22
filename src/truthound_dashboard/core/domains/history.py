"""History domain services."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import timedelta
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db import Validation
from truthound_dashboard.time import utc_now


class HistoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_history(
        self,
        source_id: str,
        *,
        period: Literal["7d", "30d", "90d"] = "30d",
        granularity: Literal["hourly", "daily", "weekly"] = "daily",
    ) -> dict[str, Any]:
        days = {"7d": 7, "30d": 30, "90d": 90}[period]
        start_date = utc_now() - timedelta(days=days)

        result = await self.session.execute(
            select(Validation)
            .where(Validation.source_id == source_id)
            .where(Validation.created_at >= start_date)
            .order_by(Validation.created_at.desc())
        )
        validations = list(result.scalars().all())
        total_runs = len(validations)
        passed_runs = sum(1 for validation in validations if validation.passed)
        failed_runs = sum(1 for validation in validations if validation.passed is False)
        success_rate = (passed_runs / total_runs * 100) if total_runs > 0 else 0

        return {
            "summary": {
                "total_runs": total_runs,
                "passed_runs": passed_runs,
                "failed_runs": failed_runs,
                "success_rate": round(success_rate, 2),
            },
            "trend": self._aggregate_by_period(validations, granularity),
            "failure_frequency": self._calculate_failure_frequency(validations),
            "recent_validations": [
                {
                    "id": validation.id,
                    "status": validation.status,
                    "passed": validation.passed,
                    "has_critical": validation.has_critical,
                    "has_high": validation.has_high,
                    "total_issues": validation.total_issues,
                    "created_at": validation.created_at.isoformat(),
                }
                for validation in validations[:10]
            ],
        }

    def _aggregate_by_period(
        self,
        validations: list[Validation],
        granularity: Literal["hourly", "daily", "weekly"],
    ) -> list[dict[str, Any]]:
        buckets: dict[str, list[Validation]] = defaultdict(list)
        for validation in validations:
            if granularity == "hourly":
                key = validation.created_at.strftime("%Y-%m-%d %H:00")
            elif granularity == "daily":
                key = validation.created_at.strftime("%Y-%m-%d")
            else:
                monday = validation.created_at - timedelta(days=validation.created_at.weekday())
                key = monday.strftime("%Y-%m-%d")
            buckets[key].append(validation)

        trend = []
        for date, bucket in sorted(buckets.items()):
            passed_count = sum(1 for validation in bucket if validation.passed)
            success_rate = (passed_count / len(bucket) * 100) if bucket else 0
            trend.append(
                {
                    "date": date,
                    "success_rate": round(success_rate, 2),
                    "run_count": len(bucket),
                    "passed_count": passed_count,
                    "failed_count": len(bucket) - passed_count,
                }
            )
        return trend

    def _calculate_failure_frequency(self, validations: list[Validation]) -> list[dict[str, Any]]:
        failures: Counter[str] = Counter()
        for validation in validations:
            if validation.result_json and "issues" in validation.result_json:
                for issue in validation.result_json["issues"]:
                    key = f"{issue.get('column', 'unknown')}.{issue.get('issue_type', 'unknown')}"
                    failures[key] += issue.get("count", 1)
        return [{"issue": issue, "count": count} for issue, count in failures.most_common(10)]


__all__ = ["HistoryService"]
