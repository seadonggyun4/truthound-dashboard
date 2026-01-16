"""Storage backends for escalation state.

This module provides storage backends for persisting escalation
policies and incidents.

Storage Backends:
    - InMemoryEscalationStore: Simple in-memory storage
    - SQLiteEscalationStore: Persistent SQLite storage
"""

from __future__ import annotations

import json
import sqlite3
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import EscalationIncident, EscalationPolicy, EscalationState


class BaseEscalationStore(ABC):
    """Abstract base class for escalation storage."""

    # Policy operations
    @abstractmethod
    def save_policy(self, policy: EscalationPolicy) -> str:
        """Save or update a policy."""
        ...

    @abstractmethod
    def get_policy(self, policy_id: str) -> EscalationPolicy | None:
        """Get policy by ID."""
        ...

    @abstractmethod
    def get_policy_by_name(self, name: str) -> EscalationPolicy | None:
        """Get policy by name."""
        ...

    @abstractmethod
    def list_policies(self, active_only: bool = True) -> list[EscalationPolicy]:
        """List all policies."""
        ...

    @abstractmethod
    def delete_policy(self, policy_id: str) -> bool:
        """Delete a policy."""
        ...

    # Incident operations
    @abstractmethod
    def save_incident(self, incident: EscalationIncident) -> str:
        """Save or update an incident."""
        ...

    @abstractmethod
    def get_incident(self, incident_id: str) -> EscalationIncident | None:
        """Get incident by ID."""
        ...

    @abstractmethod
    def get_incident_by_ref(self, incident_ref: str) -> EscalationIncident | None:
        """Get incident by external reference."""
        ...

    @abstractmethod
    def list_incidents(
        self,
        policy_id: str | None = None,
        states: list[EscalationState] | None = None,
    ) -> list[EscalationIncident]:
        """List incidents with optional filters."""
        ...

    @abstractmethod
    def get_pending_escalations(self) -> list[EscalationIncident]:
        """Get incidents due for escalation."""
        ...


class InMemoryEscalationStore(BaseEscalationStore):
    """In-memory escalation storage.

    Simple thread-safe storage suitable for development
    and testing.
    """

    def __init__(self) -> None:
        """Initialize in-memory store."""
        self._policies: dict[str, EscalationPolicy] = {}
        self._incidents: dict[str, EscalationIncident] = {}
        self._policy_counter = 0
        self._incident_counter = 0
        self._lock = threading.RLock()

    def _generate_policy_id(self) -> str:
        """Generate unique policy ID."""
        self._policy_counter += 1
        return f"policy-{self._policy_counter}"

    def _generate_incident_id(self) -> str:
        """Generate unique incident ID."""
        self._incident_counter += 1
        return f"incident-{self._incident_counter}"

    def save_policy(self, policy: EscalationPolicy) -> str:
        """Save or update a policy."""
        with self._lock:
            if not policy.id:
                policy.id = self._generate_policy_id()
            self._policies[policy.id] = policy
            return policy.id

    def get_policy(self, policy_id: str) -> EscalationPolicy | None:
        """Get policy by ID."""
        with self._lock:
            return self._policies.get(policy_id)

    def get_policy_by_name(self, name: str) -> EscalationPolicy | None:
        """Get policy by name."""
        with self._lock:
            for policy in self._policies.values():
                if policy.name == name:
                    return policy
            return None

    def list_policies(self, active_only: bool = True) -> list[EscalationPolicy]:
        """List all policies."""
        with self._lock:
            policies = list(self._policies.values())
            if active_only:
                policies = [p for p in policies if p.is_active]
            return policies

    def delete_policy(self, policy_id: str) -> bool:
        """Delete a policy."""
        with self._lock:
            if policy_id in self._policies:
                del self._policies[policy_id]
                return True
            return False

    def save_incident(self, incident: EscalationIncident) -> str:
        """Save or update an incident."""
        with self._lock:
            if not incident.id:
                incident.id = self._generate_incident_id()
            incident.updated_at = datetime.utcnow()
            self._incidents[incident.id] = incident
            return incident.id

    def get_incident(self, incident_id: str) -> EscalationIncident | None:
        """Get incident by ID."""
        with self._lock:
            return self._incidents.get(incident_id)

    def get_incident_by_ref(self, incident_ref: str) -> EscalationIncident | None:
        """Get incident by external reference."""
        with self._lock:
            for incident in self._incidents.values():
                if incident.incident_ref == incident_ref:
                    return incident
            return None

    def list_incidents(
        self,
        policy_id: str | None = None,
        states: list[EscalationState] | None = None,
    ) -> list[EscalationIncident]:
        """List incidents with optional filters."""
        with self._lock:
            incidents = list(self._incidents.values())

            if policy_id:
                incidents = [i for i in incidents if i.policy_id == policy_id]

            if states:
                incidents = [i for i in incidents if i.state in states]

            return incidents

    def get_pending_escalations(self) -> list[EscalationIncident]:
        """Get incidents due for escalation."""
        now = datetime.utcnow()
        active_states = [
            EscalationState.TRIGGERED,
            EscalationState.ESCALATED,
        ]

        with self._lock:
            return [
                i for i in self._incidents.values()
                if i.state in active_states
                and i.next_escalation_at
                and i.next_escalation_at <= now
            ]


class SQLiteEscalationStore(BaseEscalationStore):
    """SQLite-based persistent escalation storage."""

    def __init__(self, db_path: str | Path = "escalation.db") -> None:
        """Initialize SQLite store."""
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

        # Policies table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS escalation_policies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                levels TEXT NOT NULL,
                auto_resolve_on_success INTEGER NOT NULL DEFAULT 1,
                max_escalations INTEGER NOT NULL DEFAULT 3,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Incidents table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS escalation_incidents (
                id TEXT PRIMARY KEY,
                policy_id TEXT NOT NULL,
                incident_ref TEXT NOT NULL UNIQUE,
                state TEXT NOT NULL,
                current_level INTEGER NOT NULL DEFAULT 0,
                context TEXT,
                acknowledged_by TEXT,
                acknowledged_at TEXT,
                resolved_by TEXT,
                resolved_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                next_escalation_at TEXT,
                escalation_count INTEGER NOT NULL DEFAULT 0,
                events TEXT,
                FOREIGN KEY (policy_id) REFERENCES escalation_policies(id)
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_incident_state
            ON escalation_incidents(state)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_incident_next_escalation
            ON escalation_incidents(next_escalation_at)
        """)

        conn.commit()

    def save_policy(self, policy: EscalationPolicy) -> str:
        """Save or update a policy."""
        conn = self._get_connection()
        now = datetime.utcnow().isoformat()

        if not policy.id:
            import uuid
            policy.id = str(uuid.uuid4())

        levels_json = json.dumps([l.to_dict() for l in policy.levels])

        conn.execute(
            """
            INSERT OR REPLACE INTO escalation_policies
            (id, name, description, levels, auto_resolve_on_success,
             max_escalations, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                policy.id,
                policy.name,
                policy.description,
                levels_json,
                1 if policy.auto_resolve_on_success else 0,
                policy.max_escalations,
                1 if policy.is_active else 0,
                now,
                now,
            ),
        )
        conn.commit()
        return policy.id

    def get_policy(self, policy_id: str) -> EscalationPolicy | None:
        """Get policy by ID."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM escalation_policies WHERE id = ?",
            (policy_id,),
        )
        row = cursor.fetchone()
        return self._row_to_policy(row) if row else None

    def get_policy_by_name(self, name: str) -> EscalationPolicy | None:
        """Get policy by name."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM escalation_policies WHERE name = ?",
            (name,),
        )
        row = cursor.fetchone()
        return self._row_to_policy(row) if row else None

    def list_policies(self, active_only: bool = True) -> list[EscalationPolicy]:
        """List all policies."""
        conn = self._get_connection()
        if active_only:
            cursor = conn.execute(
                "SELECT * FROM escalation_policies WHERE is_active = 1"
            )
        else:
            cursor = conn.execute("SELECT * FROM escalation_policies")

        return [self._row_to_policy(row) for row in cursor.fetchall()]

    def delete_policy(self, policy_id: str) -> bool:
        """Delete a policy."""
        conn = self._get_connection()
        cursor = conn.execute(
            "DELETE FROM escalation_policies WHERE id = ?",
            (policy_id,),
        )
        conn.commit()
        return cursor.rowcount > 0

    def _row_to_policy(self, row: sqlite3.Row) -> EscalationPolicy:
        """Convert database row to policy."""
        from .models import EscalationLevel

        levels_data = json.loads(row["levels"])
        levels = [EscalationLevel.from_dict(l) for l in levels_data]

        return EscalationPolicy(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            levels=levels,
            auto_resolve_on_success=bool(row["auto_resolve_on_success"]),
            max_escalations=row["max_escalations"],
            is_active=bool(row["is_active"]),
        )

    def save_incident(self, incident: EscalationIncident) -> str:
        """Save or update an incident."""
        conn = self._get_connection()
        now = datetime.utcnow().isoformat()

        if not incident.id:
            import uuid
            incident.id = str(uuid.uuid4())

        incident.updated_at = datetime.utcnow()

        conn.execute(
            """
            INSERT OR REPLACE INTO escalation_incidents
            (id, policy_id, incident_ref, state, current_level, context,
             acknowledged_by, acknowledged_at, resolved_by, resolved_at,
             created_at, updated_at, next_escalation_at, escalation_count, events)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                incident.id,
                incident.policy_id,
                incident.incident_ref,
                incident.state.value,
                incident.current_level,
                json.dumps(incident.context),
                incident.acknowledged_by,
                incident.acknowledged_at.isoformat() if incident.acknowledged_at else None,
                incident.resolved_by,
                incident.resolved_at.isoformat() if incident.resolved_at else None,
                incident.created_at.isoformat(),
                incident.updated_at.isoformat(),
                incident.next_escalation_at.isoformat() if incident.next_escalation_at else None,
                incident.escalation_count,
                json.dumps([e.to_dict() for e in incident.events]),
            ),
        )
        conn.commit()
        return incident.id

    def get_incident(self, incident_id: str) -> EscalationIncident | None:
        """Get incident by ID."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM escalation_incidents WHERE id = ?",
            (incident_id,),
        )
        row = cursor.fetchone()
        return self._row_to_incident(row) if row else None

    def get_incident_by_ref(self, incident_ref: str) -> EscalationIncident | None:
        """Get incident by external reference."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM escalation_incidents WHERE incident_ref = ?",
            (incident_ref,),
        )
        row = cursor.fetchone()
        return self._row_to_incident(row) if row else None

    def list_incidents(
        self,
        policy_id: str | None = None,
        states: list[EscalationState] | None = None,
    ) -> list[EscalationIncident]:
        """List incidents with optional filters."""
        conn = self._get_connection()

        query = "SELECT * FROM escalation_incidents WHERE 1=1"
        params: list[Any] = []

        if policy_id:
            query += " AND policy_id = ?"
            params.append(policy_id)

        if states:
            placeholders = ",".join("?" * len(states))
            query += f" AND state IN ({placeholders})"
            params.extend(s.value for s in states)

        cursor = conn.execute(query, params)
        return [self._row_to_incident(row) for row in cursor.fetchall()]

    def get_pending_escalations(self) -> list[EscalationIncident]:
        """Get incidents due for escalation."""
        now = datetime.utcnow().isoformat()
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT * FROM escalation_incidents
            WHERE state IN (?, ?)
            AND next_escalation_at IS NOT NULL
            AND next_escalation_at <= ?
            """,
            (EscalationState.TRIGGERED.value, EscalationState.ESCALATED.value, now),
        )
        return [self._row_to_incident(row) for row in cursor.fetchall()]

    def _row_to_incident(self, row: sqlite3.Row) -> EscalationIncident:
        """Convert database row to incident."""
        from .models import EscalationEvent

        events_data = json.loads(row["events"]) if row["events"] else []
        events = [EscalationEvent.from_dict(e) for e in events_data]

        return EscalationIncident(
            id=row["id"],
            policy_id=row["policy_id"],
            incident_ref=row["incident_ref"],
            state=EscalationState(row["state"]),
            current_level=row["current_level"],
            context=json.loads(row["context"]) if row["context"] else {},
            acknowledged_by=row["acknowledged_by"],
            acknowledged_at=datetime.fromisoformat(row["acknowledged_at"]) if row["acknowledged_at"] else None,
            resolved_by=row["resolved_by"],
            resolved_at=datetime.fromisoformat(row["resolved_at"]) if row["resolved_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            next_escalation_at=datetime.fromisoformat(row["next_escalation_at"]) if row["next_escalation_at"] else None,
            escalation_count=row["escalation_count"],
            events=events,
        )

    def close(self) -> None:
        """Close database connection."""
        if hasattr(self._local, "connection"):
            self._local.connection.close()
            del self._local.connection
