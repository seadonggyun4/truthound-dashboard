"""UTC time helpers for dashboard code.

The dashboard currently persists naive UTC datetimes in several database tables.
These helpers avoid deprecated ``datetime.utcnow()`` calls while preserving the
existing naive-UTC storage semantics until a future timezone-aware migration.
"""

from __future__ import annotations

from datetime import UTC, date, datetime


def utc_now() -> datetime:
    """Return the current time as a naive UTC datetime."""

    return datetime.now(UTC).replace(tzinfo=None)


def utc_today() -> date:
    """Return today's date in UTC."""

    return utc_now().date()
