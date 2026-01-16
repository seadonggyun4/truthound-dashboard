"""Storage backends for deduplication state.

This module provides storage backends for tracking sent notifications
and detecting duplicates.

Storage Backends:
    - InMemoryDeduplicationStore: Simple in-memory storage (development)
    - SQLiteDeduplicationStore: Persistent SQLite storage (production)

Each store tracks fingerprints with timestamps and supports
automatic cleanup of expired entries.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass
class DeduplicationEntry:
    """A stored deduplication entry.

    Attributes:
        fingerprint: Unique fingerprint identifying the notification.
        first_seen: When this fingerprint was first seen.
        last_seen: When this fingerprint was last seen.
        count: Number of times this fingerprint was seen.
        metadata: Additional entry metadata.
    """

    fingerprint: str
    first_seen: datetime
    last_seen: datetime
    count: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self, window_seconds: int) -> bool:
        """Check if entry has expired based on window."""
        expiry = self.last_seen + timedelta(seconds=window_seconds)
        return datetime.utcnow() > expiry


class BaseDeduplicationStore(ABC):
    """Abstract base class for deduplication storage.

    All stores must implement methods for checking, recording,
    and cleaning up deduplication entries.
    """

    @abstractmethod
    def exists(self, fingerprint: str, window_seconds: int) -> bool:
        """Check if fingerprint exists within window.

        Args:
            fingerprint: The fingerprint to check.
            window_seconds: Time window in seconds.

        Returns:
            True if fingerprint exists and is not expired.
        """
        ...

    @abstractmethod
    def record(self, fingerprint: str, metadata: dict[str, Any] | None = None) -> None:
        """Record a fingerprint as sent.

        Args:
            fingerprint: The fingerprint to record.
            metadata: Optional metadata to store.
        """
        ...

    @abstractmethod
    def get(self, fingerprint: str) -> DeduplicationEntry | None:
        """Get entry by fingerprint.

        Args:
            fingerprint: The fingerprint to look up.

        Returns:
            Entry if found, None otherwise.
        """
        ...

    @abstractmethod
    def cleanup(self, max_age_seconds: int) -> int:
        """Remove expired entries.

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

    @abstractmethod
    def count(self) -> int:
        """Get total entry count."""
        ...


class InMemoryDeduplicationStore(BaseDeduplicationStore):
    """In-memory deduplication storage.

    Simple thread-safe in-memory storage suitable for
    development and single-process deployments.

    Note: Data is lost on process restart.
    """

    def __init__(self) -> None:
        """Initialize in-memory store."""
        self._entries: dict[str, DeduplicationEntry] = {}
        self._lock = threading.RLock()

    def exists(self, fingerprint: str, window_seconds: int) -> bool:
        """Check if fingerprint exists within window."""
        with self._lock:
            entry = self._entries.get(fingerprint)
            if entry is None:
                return False
            return not entry.is_expired(window_seconds)

    def record(self, fingerprint: str, metadata: dict[str, Any] | None = None) -> None:
        """Record a fingerprint."""
        now = datetime.utcnow()
        with self._lock:
            if fingerprint in self._entries:
                entry = self._entries[fingerprint]
                entry.last_seen = now
                entry.count += 1
                if metadata:
                    entry.metadata.update(metadata)
            else:
                self._entries[fingerprint] = DeduplicationEntry(
                    fingerprint=fingerprint,
                    first_seen=now,
                    last_seen=now,
                    count=1,
                    metadata=metadata or {},
                )

    def get(self, fingerprint: str) -> DeduplicationEntry | None:
        """Get entry by fingerprint."""
        with self._lock:
            return self._entries.get(fingerprint)

    def cleanup(self, max_age_seconds: int) -> int:
        """Remove expired entries."""
        cutoff = datetime.utcnow() - timedelta(seconds=max_age_seconds)
        removed = 0

        with self._lock:
            expired = [
                fp for fp, entry in self._entries.items()
                if entry.last_seen < cutoff
            ]
            for fp in expired:
                del self._entries[fp]
                removed += 1

        return removed

    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._entries.clear()

    def count(self) -> int:
        """Get total entry count."""
        with self._lock:
            return len(self._entries)


class SQLiteDeduplicationStore(BaseDeduplicationStore):
    """SQLite-based persistent deduplication storage.

    Provides durable storage that survives process restarts.
    Thread-safe using connection pooling.

    Attributes:
        db_path: Path to SQLite database file.
    """

    def __init__(self, db_path: str | Path = "deduplication.db") -> None:
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
            CREATE TABLE IF NOT EXISTS deduplication_entries (
                fingerprint TEXT PRIMARY KEY,
                first_seen REAL NOT NULL,
                last_seen REAL NOT NULL,
                count INTEGER NOT NULL DEFAULT 1,
                metadata TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_dedup_last_seen
            ON deduplication_entries(last_seen)
        """)
        conn.commit()

    def exists(self, fingerprint: str, window_seconds: int) -> bool:
        """Check if fingerprint exists within window."""
        conn = self._get_connection()
        cutoff = time.time() - window_seconds

        cursor = conn.execute(
            """
            SELECT 1 FROM deduplication_entries
            WHERE fingerprint = ? AND last_seen >= ?
            """,
            (fingerprint, cutoff),
        )
        return cursor.fetchone() is not None

    def record(self, fingerprint: str, metadata: dict[str, Any] | None = None) -> None:
        """Record a fingerprint."""
        import json

        now = time.time()
        conn = self._get_connection()

        # Try to update existing
        cursor = conn.execute(
            """
            UPDATE deduplication_entries
            SET last_seen = ?, count = count + 1
            WHERE fingerprint = ?
            """,
            (now, fingerprint),
        )

        if cursor.rowcount == 0:
            # Insert new entry
            metadata_json = json.dumps(metadata) if metadata else None
            conn.execute(
                """
                INSERT INTO deduplication_entries
                (fingerprint, first_seen, last_seen, count, metadata)
                VALUES (?, ?, ?, 1, ?)
                """,
                (fingerprint, now, now, metadata_json),
            )

        conn.commit()

    def get(self, fingerprint: str) -> DeduplicationEntry | None:
        """Get entry by fingerprint."""
        import json

        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT fingerprint, first_seen, last_seen, count, metadata
            FROM deduplication_entries
            WHERE fingerprint = ?
            """,
            (fingerprint,),
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

        return DeduplicationEntry(
            fingerprint=row["fingerprint"],
            first_seen=datetime.fromtimestamp(row["first_seen"]),
            last_seen=datetime.fromtimestamp(row["last_seen"]),
            count=row["count"],
            metadata=metadata,
        )

    def cleanup(self, max_age_seconds: int) -> int:
        """Remove expired entries."""
        conn = self._get_connection()
        cutoff = time.time() - max_age_seconds

        cursor = conn.execute(
            """
            DELETE FROM deduplication_entries
            WHERE last_seen < ?
            """,
            (cutoff,),
        )
        conn.commit()

        return cursor.rowcount

    def clear(self) -> None:
        """Clear all entries."""
        conn = self._get_connection()
        conn.execute("DELETE FROM deduplication_entries")
        conn.commit()

    def count(self) -> int:
        """Get total entry count."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM deduplication_entries")
        return cursor.fetchone()[0]

    def close(self) -> None:
        """Close database connection."""
        if hasattr(self._local, "connection"):
            self._local.connection.close()
            del self._local.connection
