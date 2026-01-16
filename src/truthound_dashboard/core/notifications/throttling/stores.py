"""Storage backends for throttling state.

This module provides storage backends for tracking rate limit
counters and token buckets.

Storage Backends:
    - InMemoryThrottlingStore: Simple in-memory storage
    - SQLiteThrottlingStore: Persistent SQLite storage
"""

from __future__ import annotations

import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ThrottlingEntry:
    """A stored throttling entry.

    Attributes:
        key: Unique key identifying the throttled entity.
        count: Current count within the window.
        window_start: Start of the current window.
        tokens: Current token count (for token bucket).
        last_refill: Last token refill time.
    """

    key: str
    count: int = 0
    window_start: float = 0.0
    tokens: float = 0.0
    last_refill: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseThrottlingStore(ABC):
    """Abstract base class for throttling storage.

    All stores must implement methods for getting and updating
    throttling state.
    """

    @abstractmethod
    def get(self, key: str) -> ThrottlingEntry | None:
        """Get entry by key.

        Args:
            key: The throttling key.

        Returns:
            Entry if found, None otherwise.
        """
        ...

    @abstractmethod
    def set(self, entry: ThrottlingEntry) -> None:
        """Set or update an entry.

        Args:
            entry: The entry to store.
        """
        ...

    @abstractmethod
    def increment(self, key: str, window_start: float) -> int:
        """Increment counter and return new count.

        If the entry doesn't exist or window has changed,
        creates a new entry with count=1.

        Args:
            key: The throttling key.
            window_start: Start of current window.

        Returns:
            New count value.
        """
        ...

    @abstractmethod
    def cleanup(self, max_age_seconds: int) -> int:
        """Remove old entries.

        Args:
            max_age_seconds: Maximum age of entries to keep.

        Returns:
            Number of entries removed.
        """
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear all entries."""
        ...


class InMemoryThrottlingStore(BaseThrottlingStore):
    """In-memory throttling storage.

    Simple thread-safe storage suitable for development
    and single-process deployments.
    """

    def __init__(self) -> None:
        """Initialize in-memory store."""
        self._entries: dict[str, ThrottlingEntry] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> ThrottlingEntry | None:
        """Get entry by key."""
        with self._lock:
            return self._entries.get(key)

    def set(self, entry: ThrottlingEntry) -> None:
        """Set or update an entry."""
        with self._lock:
            self._entries[entry.key] = entry

    def increment(self, key: str, window_start: float) -> int:
        """Increment counter and return new count."""
        with self._lock:
            entry = self._entries.get(key)

            if entry is None or entry.window_start != window_start:
                # New window
                entry = ThrottlingEntry(
                    key=key,
                    count=1,
                    window_start=window_start,
                )
                self._entries[key] = entry
                return 1

            # Same window, increment
            entry.count += 1
            return entry.count

    def cleanup(self, max_age_seconds: int) -> int:
        """Remove old entries."""
        cutoff = time.time() - max_age_seconds
        removed = 0

        with self._lock:
            expired = [
                key for key, entry in self._entries.items()
                if entry.window_start < cutoff
            ]
            for key in expired:
                del self._entries[key]
                removed += 1

        return removed

    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._entries.clear()


class SQLiteThrottlingStore(BaseThrottlingStore):
    """SQLite-based persistent throttling storage.

    Provides durable storage that survives process restarts.
    """

    def __init__(self, db_path: str | Path = "throttling.db") -> None:
        """Initialize SQLite store.

        Args:
            db_path: Path to database file.
        """
        self.db_path = Path(db_path)
        self._local = threading.local()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, "connection"):
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS throttling_entries (
                key TEXT PRIMARY KEY,
                count INTEGER NOT NULL DEFAULT 0,
                window_start REAL NOT NULL,
                tokens REAL NOT NULL DEFAULT 0,
                last_refill REAL NOT NULL DEFAULT 0,
                metadata TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_throttle_window
            ON throttling_entries(window_start)
        """)
        conn.commit()

    def get(self, key: str) -> ThrottlingEntry | None:
        """Get entry by key."""
        import json

        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT key, count, window_start, tokens, last_refill, metadata
            FROM throttling_entries
            WHERE key = ?
            """,
            (key,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        metadata = {}
        if row["metadata"]:
            try:
                metadata = json.loads(row["metadata"])
            except json.JSONDecodeError:
                pass

        return ThrottlingEntry(
            key=row["key"],
            count=row["count"],
            window_start=row["window_start"],
            tokens=row["tokens"],
            last_refill=row["last_refill"],
            metadata=metadata,
        )

    def set(self, entry: ThrottlingEntry) -> None:
        """Set or update an entry."""
        import json

        conn = self._get_connection()
        metadata_json = json.dumps(entry.metadata) if entry.metadata else None

        conn.execute(
            """
            INSERT OR REPLACE INTO throttling_entries
            (key, count, window_start, tokens, last_refill, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                entry.key,
                entry.count,
                entry.window_start,
                entry.tokens,
                entry.last_refill,
                metadata_json,
            ),
        )
        conn.commit()

    def increment(self, key: str, window_start: float) -> int:
        """Increment counter and return new count."""
        conn = self._get_connection()

        # Check if entry exists and is in same window
        cursor = conn.execute(
            """
            SELECT count, window_start FROM throttling_entries
            WHERE key = ?
            """,
            (key,),
        )
        row = cursor.fetchone()

        if row is None or row["window_start"] != window_start:
            # New window
            conn.execute(
                """
                INSERT OR REPLACE INTO throttling_entries
                (key, count, window_start, tokens, last_refill)
                VALUES (?, 1, ?, 0, 0)
                """,
                (key, window_start),
            )
            conn.commit()
            return 1

        # Same window, increment
        conn.execute(
            """
            UPDATE throttling_entries
            SET count = count + 1
            WHERE key = ?
            """,
            (key,),
        )
        conn.commit()

        return row["count"] + 1

    def cleanup(self, max_age_seconds: int) -> int:
        """Remove old entries."""
        conn = self._get_connection()
        cutoff = time.time() - max_age_seconds

        cursor = conn.execute(
            """
            DELETE FROM throttling_entries
            WHERE window_start < ?
            """,
            (cutoff,),
        )
        conn.commit()

        return cursor.rowcount

    def clear(self) -> None:
        """Clear all entries."""
        conn = self._get_connection()
        conn.execute("DELETE FROM throttling_entries")
        conn.commit()

    def close(self) -> None:
        """Close database connection."""
        if hasattr(self._local, "connection"):
            self._local.connection.close()
            del self._local.connection
