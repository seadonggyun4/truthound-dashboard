"""Database module.

This module provides database connectivity, models, and repository patterns
for the truthound dashboard.

Exports:
    - Database connection: get_session, get_db_session, init_db
    - Base classes: Base, UUIDMixin, TimestampMixin
    - Models: Source, Schema, Rule, Validation, Profile, Schedule, DriftComparison, AppSettings
    - Repository: BaseRepository
"""

from .base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from .database import (
    get_db_session,
    get_engine,
    get_session,
    get_session_factory,
    init_db,
    reset_connection,
    reset_db,
)
from .models import (
    AppSettings,
    DriftComparison,
    Profile,
    Rule,
    Schedule,
    Schema,
    Source,
    Validation,
)
from .repository import BaseRepository

__all__ = [
    # Base classes
    "Base",
    "UUIDMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    # Database functions
    "get_session",
    "get_db_session",
    "get_engine",
    "get_session_factory",
    "init_db",
    "reset_db",
    "reset_connection",
    # Models
    "Source",
    "Schema",
    "Rule",
    "Validation",
    "Profile",
    "Schedule",
    "DriftComparison",
    "AppSettings",
    # Repository
    "BaseRepository",
]
