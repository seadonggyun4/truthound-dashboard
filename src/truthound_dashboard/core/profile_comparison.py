"""Profile comparison service.

This module provides functionality for comparing profiles
over time, including time-series trends and version comparison.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db import Profile, Source
from truthound_dashboard.core.services import ProfileRepository
from truthound_dashboard.schemas.profile_comparison import (
    ColumnComparison,
    ColumnTrend,
    LatestComparisonResponse,
    ProfileComparisonResponse,
    ProfileSummary,
    ProfileTrendPoint,
    ProfileTrendResponse,
    TrendDirection,
)


def _parse_percentage(value: str | None) -> float:
    """Parse percentage string to float.

    Args:
        value: Percentage string like "25.5%".

    Returns:
        Float value (0.0-100.0).
    """
    if not value:
        return 0.0
    try:
        return float(value.replace("%", ""))
    except (ValueError, AttributeError):
        return 0.0


def _calculate_change(baseline: float, current: float) -> tuple[float, float | None]:
    """Calculate absolute and percentage change.

    Args:
        baseline: Baseline value.
        current: Current value.

    Returns:
        Tuple of (absolute_change, percentage_change).
    """
    change = current - baseline
    if baseline != 0:
        change_pct = (change / baseline) * 100
    else:
        change_pct = None
    return change, change_pct


def _determine_trend(change: float, threshold: float = 0.1) -> TrendDirection:
    """Determine trend direction based on change.

    Args:
        change: Change value (or percentage).
        threshold: Threshold for significant change.

    Returns:
        Trend direction.
    """
    if abs(change) < threshold:
        return TrendDirection.STABLE
    return TrendDirection.UP if change > 0 else TrendDirection.DOWN


class ProfileComparisonService:
    """Service for profile comparison and trend analysis."""

    def __init__(self, session: AsyncSession):
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.profile_repo = ProfileRepository(session)

    async def list_profiles(
        self,
        source_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ProfileSummary]:
        """List profile history for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.
            offset: Number to skip.

        Returns:
            List of profile summaries.
        """
        profiles = await self.profile_repo.get_for_source(
            source_id, limit=limit, offset=offset
        )
        return [
            ProfileSummary(
                id=p.id,
                source_id=p.source_id,
                row_count=p.row_count or 0,
                column_count=p.column_count or 0,
                size_bytes=p.size_bytes or 0,
                created_at=p.created_at,
            )
            for p in profiles
        ]

    def _compare_columns(
        self,
        baseline_cols: list[dict[str, Any]],
        current_cols: list[dict[str, Any]],
        significance_threshold: float = 0.1,
    ) -> list[ColumnComparison]:
        """Compare column statistics between two profiles.

        Args:
            baseline_cols: Baseline column profiles.
            current_cols: Current column profiles.
            significance_threshold: Threshold for significant change.

        Returns:
            List of column comparisons.
        """
        comparisons = []

        # Create lookup by column name
        baseline_map = {c.get("name"): c for c in baseline_cols}
        current_map = {c.get("name"): c for c in current_cols}

        # Compare columns present in both
        common_cols = set(baseline_map.keys()) & set(current_map.keys())

        for col_name in common_cols:
            baseline = baseline_map[col_name]
            current = current_map[col_name]

            # Compare null_pct
            baseline_null = _parse_percentage(baseline.get("null_pct"))
            current_null = _parse_percentage(current.get("null_pct"))
            null_change, null_change_pct = _calculate_change(baseline_null, current_null)
            is_null_significant = abs(null_change) >= significance_threshold * 100

            comparisons.append(
                ColumnComparison(
                    column=col_name,
                    metric="null_pct",
                    baseline_value=baseline_null,
                    current_value=current_null,
                    change=null_change,
                    change_pct=null_change_pct,
                    is_significant=is_null_significant,
                    trend=_determine_trend(null_change, significance_threshold * 100),
                )
            )

            # Compare unique_pct
            baseline_unique = _parse_percentage(baseline.get("unique_pct"))
            current_unique = _parse_percentage(current.get("unique_pct"))
            unique_change, unique_change_pct = _calculate_change(
                baseline_unique, current_unique
            )
            is_unique_significant = abs(unique_change) >= significance_threshold * 100

            comparisons.append(
                ColumnComparison(
                    column=col_name,
                    metric="unique_pct",
                    baseline_value=baseline_unique,
                    current_value=current_unique,
                    change=unique_change,
                    change_pct=unique_change_pct,
                    is_significant=is_unique_significant,
                    trend=_determine_trend(unique_change, significance_threshold * 100),
                )
            )

            # Compare distinct_count if available
            baseline_distinct = baseline.get("distinct_count")
            current_distinct = current.get("distinct_count")
            if baseline_distinct is not None and current_distinct is not None:
                distinct_change, distinct_change_pct = _calculate_change(
                    float(baseline_distinct), float(current_distinct)
                )
                is_distinct_significant = (
                    distinct_change_pct is not None
                    and abs(distinct_change_pct) >= significance_threshold * 100
                )

                comparisons.append(
                    ColumnComparison(
                        column=col_name,
                        metric="distinct_count",
                        baseline_value=baseline_distinct,
                        current_value=current_distinct,
                        change=distinct_change,
                        change_pct=distinct_change_pct,
                        is_significant=is_distinct_significant,
                        trend=_determine_trend(
                            distinct_change_pct or 0, significance_threshold * 100
                        ),
                    )
                )

        return comparisons

    async def compare_profiles(
        self,
        source: Source,
        baseline_profile_id: str,
        current_profile_id: str,
        *,
        significance_threshold: float = 0.1,
    ) -> ProfileComparisonResponse:
        """Compare two specific profiles.

        Args:
            source: Source record.
            baseline_profile_id: Baseline profile ID.
            current_profile_id: Current profile ID.
            significance_threshold: Threshold for significant changes.

        Returns:
            Profile comparison response.
        """
        # Load profiles
        baseline = await self.profile_repo.get_by_id(baseline_profile_id)
        current = await self.profile_repo.get_by_id(current_profile_id)

        if not baseline or not current:
            raise ValueError("One or both profiles not found")

        # Get row count changes
        baseline_rows = baseline.row_count or 0
        current_rows = current.row_count or 0
        row_change, row_change_pct = _calculate_change(
            float(baseline_rows), float(current_rows)
        )

        # Get column count changes
        baseline_cols = baseline.column_count or 0
        current_cols = current.column_count or 0
        col_change = current_cols - baseline_cols

        # Compare columns
        baseline_columns = baseline.columns if hasattr(baseline, "columns") else []
        current_columns = current.columns if hasattr(current, "columns") else []

        if not baseline_columns and baseline.profile_json:
            baseline_columns = baseline.profile_json.get("columns", [])
        if not current_columns and current.profile_json:
            current_columns = current.profile_json.get("columns", [])

        column_comparisons = self._compare_columns(
            baseline_columns, current_columns, significance_threshold
        )

        # Count significant changes
        significant_count = sum(1 for c in column_comparisons if c.is_significant)

        # Build summary
        summary = {
            "baseline_date": baseline.created_at.isoformat(),
            "current_date": current.created_at.isoformat(),
            "time_diff_hours": (
                current.created_at - baseline.created_at
            ).total_seconds() / 3600,
            "columns_compared": len(set(c.column for c in column_comparisons)),
        }

        return ProfileComparisonResponse(
            source_id=source.id,
            source_name=source.name,
            baseline_profile_id=baseline_profile_id,
            current_profile_id=current_profile_id,
            baseline_timestamp=baseline.created_at,
            current_timestamp=current.created_at,
            row_count_change=int(row_change),
            row_count_change_pct=row_change_pct or 0.0,
            column_count_change=col_change,
            column_comparisons=column_comparisons,
            significant_changes=significant_count,
            summary=summary,
            compared_at=datetime.utcnow(),
        )

    async def get_latest_comparison(
        self,
        source: Source,
    ) -> LatestComparisonResponse:
        """Compare latest profile with previous one.

        Args:
            source: Source record.

        Returns:
            Latest comparison response.
        """
        # Get last two profiles
        profiles = await self.profile_repo.get_for_source(source.id, limit=2)

        if len(profiles) < 2:
            return LatestComparisonResponse(
                source_id=source.id,
                has_previous=False,
                comparison=None,
            )

        current = profiles[0]
        baseline = profiles[1]

        comparison = await self.compare_profiles(
            source, baseline.id, current.id
        )

        return LatestComparisonResponse(
            source_id=source.id,
            has_previous=True,
            comparison=comparison,
        )

    def _parse_period(self, period: str) -> timedelta:
        """Parse period string to timedelta.

        Args:
            period: Period string like "30d", "7d", "90d".

        Returns:
            Timedelta object.
        """
        if period.endswith("d"):
            days = int(period[:-1])
            return timedelta(days=days)
        elif period.endswith("w"):
            weeks = int(period[:-1])
            return timedelta(weeks=weeks)
        elif period.endswith("h"):
            hours = int(period[:-1])
            return timedelta(hours=hours)
        else:
            # Default to days
            return timedelta(days=int(period))

    async def get_profile_trend(
        self,
        source: Source,
        *,
        period: str = "30d",
        granularity: str = "daily",
    ) -> ProfileTrendResponse:
        """Get time-series profile trends.

        Args:
            source: Source record.
            period: Time period (e.g., "7d", "30d", "90d").
            granularity: Data granularity (hourly, daily, weekly).

        Returns:
            Profile trend response.
        """
        # Calculate time range
        period_delta = self._parse_period(period)
        start_time = datetime.utcnow() - period_delta

        # Get profiles within period
        profiles = await self.profile_repo.get_for_source(
            source.id, limit=1000
        )
        profiles = [p for p in profiles if p.created_at >= start_time]
        profiles.sort(key=lambda p: p.created_at)

        # Build trend points
        data_points: list[ProfileTrendPoint] = []
        for profile in profiles:
            columns = profile.columns if hasattr(profile, "columns") else []
            if not columns and profile.profile_json:
                columns = profile.profile_json.get("columns", [])

            # Calculate averages
            null_pcts = [_parse_percentage(c.get("null_pct")) for c in columns]
            unique_pcts = [_parse_percentage(c.get("unique_pct")) for c in columns]

            avg_null = sum(null_pcts) / len(null_pcts) if null_pcts else 0.0
            avg_unique = sum(unique_pcts) / len(unique_pcts) if unique_pcts else 0.0

            data_points.append(
                ProfileTrendPoint(
                    timestamp=profile.created_at,
                    profile_id=profile.id,
                    row_count=profile.row_count or 0,
                    column_count=profile.column_count or 0,
                    avg_null_pct=round(avg_null, 2),
                    avg_unique_pct=round(avg_unique, 2),
                    size_bytes=profile.size_bytes or 0,
                )
            )

        # Build column trends
        column_trends: list[ColumnTrend] = []
        if len(profiles) >= 2:
            # Get all unique column names
            all_columns = set()
            for profile in profiles:
                columns = profile.columns if hasattr(profile, "columns") else []
                if not columns and profile.profile_json:
                    columns = profile.profile_json.get("columns", [])
                for col in columns:
                    all_columns.add(col.get("name", ""))

            # Build trend for top columns by null_pct
            for col_name in list(all_columns)[:10]:
                null_values: list[tuple[datetime, float]] = []

                for profile in profiles:
                    columns = profile.columns if hasattr(profile, "columns") else []
                    if not columns and profile.profile_json:
                        columns = profile.profile_json.get("columns", [])

                    for col in columns:
                        if col.get("name") == col_name:
                            null_pct = _parse_percentage(col.get("null_pct"))
                            null_values.append((profile.created_at, null_pct))

                if len(null_values) >= 2:
                    first_val = null_values[0][1]
                    last_val = null_values[-1][1]
                    change = last_val - first_val
                    change_pct = (change / first_val * 100) if first_val != 0 else 0

                    column_trends.append(
                        ColumnTrend(
                            column=col_name,
                            metric="null_pct",
                            values=null_values,
                            trend_direction=_determine_trend(change, 1.0),
                            change_pct=round(change_pct, 2),
                            min_value=min(v[1] for v in null_values),
                            max_value=max(v[1] for v in null_values),
                            avg_value=sum(v[1] for v in null_values) / len(null_values),
                        )
                    )

        # Determine overall row count trend
        row_count_trend = TrendDirection.STABLE
        if len(data_points) >= 2:
            first_rows = data_points[0].row_count
            last_rows = data_points[-1].row_count
            if first_rows > 0:
                row_pct_change = (last_rows - first_rows) / first_rows * 100
                row_count_trend = _determine_trend(row_pct_change, 5.0)

        # Build summary
        summary = {
            "start_date": start_time.isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "profile_count": len(data_points),
        }

        if data_points:
            summary["min_rows"] = min(p.row_count for p in data_points)
            summary["max_rows"] = max(p.row_count for p in data_points)
            summary["avg_rows"] = int(
                sum(p.row_count for p in data_points) / len(data_points)
            )

        return ProfileTrendResponse(
            source_id=source.id,
            source_name=source.name,
            period=period,
            granularity=granularity,
            data_points=data_points,
            column_trends=column_trends,
            total_profiles=len(data_points),
            row_count_trend=row_count_trend,
            summary=summary,
        )
