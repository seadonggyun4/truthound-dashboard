"""Database connection and session management.

This module provides async database connection handling using SQLAlchemy 2.0.
It supports both production SQLite and in-memory databases for testing.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from truthound_dashboard.config import get_settings
from truthound_dashboard.crypto import (
    decrypt_value,
    encrypt_value,
    is_sensitive_field,
    mask_sensitive_value,
)

from .base import Base
from truthound_dashboard.time import utc_now

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None

MigrationFn = Callable[[AsyncConnection], Awaitable[None]]


def _register_sqlite_datetime_adapters() -> None:
    """Register explicit SQLite adapters to avoid deprecated stdlib defaults."""

    sqlite3.register_adapter(datetime, lambda value: value.isoformat(sep=" "))
    sqlite3.register_adapter(date, lambda value: value.isoformat())


_register_sqlite_datetime_adapters()


def get_database_url(in_memory: bool = False) -> str:
    if in_memory:
        return "sqlite+aiosqlite:///:memory:"

    settings = get_settings()
    settings.ensure_directories()
    return f"sqlite+aiosqlite:///{settings.database_path}"


def get_engine(in_memory: bool = False) -> AsyncEngine:
    global _engine

    if _engine is None or in_memory:
        url = get_database_url(in_memory)
        engine = create_async_engine(
            url,
            echo=False,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False} if "sqlite" in url else {},
        )
        if not in_memory:
            _engine = engine
        return engine

    return _engine


def get_session_factory(
    engine: AsyncEngine | None = None,
) -> async_sessionmaker[AsyncSession]:
    global _session_factory

    if engine is not None:
        return async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    return _session_factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def _table_exists(conn: AsyncConnection, table_name: str) -> bool:
    result = await conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
        {"name": table_name},
    )
    return result.scalar_one_or_none() is not None


async def _list_columns(conn: AsyncConnection, table_name: str) -> list[str]:
    if not await _table_exists(conn, table_name):
        return []
    result = await conn.execute(text(f"PRAGMA table_info({table_name})"))
    return [row[1] for row in result.fetchall()]


def _default_sql_literal(default: object) -> str:
    if isinstance(default, bool):
        return "1" if default else "0"
    if isinstance(default, (int, float)):
        return str(default)
    return f"'{default}'"


async def _ensure_column(
    conn: AsyncConnection,
    table_name: str,
    column_name: str,
    column_definition: str,
    default: object | None = None,
) -> None:
    if not await _table_exists(conn, table_name):
        return
    columns = await _list_columns(conn, table_name)
    if column_name in columns:
        return

    if default is None:
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
    else:
        sql = (
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} "
            f"{column_definition} DEFAULT {_default_sql_literal(default)}"
        )

    await conn.execute(text(sql))
    logger.info("Migration: Added column %s.%s", table_name, column_name)


async def _ensure_schema_migrations_table(conn: AsyncConnection) -> None:
    await conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(100) PRIMARY KEY,
                description TEXT,
                applied_at DATETIME NOT NULL
            )
            """
        )
    )


async def _record_migration(
    conn: AsyncConnection,
    *,
    version: str,
    description: str,
) -> None:
    await conn.execute(
        text(
            """
            INSERT INTO schema_migrations (version, description, applied_at)
            VALUES (:version, :description, :applied_at)
            """
        ),
        {
            "version": version,
            "description": description,
            "applied_at": utc_now(),
        },
    )


async def _applied_migrations(conn: AsyncConnection) -> set[str]:
    await _ensure_schema_migrations_table(conn)
    result = await conn.execute(text("SELECT version FROM schema_migrations"))
    return {row[0] for row in result.fetchall()}


def _json_value(value: object | None) -> str:
    if value is None:
        return "{}"
    if isinstance(value, str):
        return value
    return json.dumps(value)


def _json_dict(value: object | None) -> dict[str, object]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return dict(parsed) if isinstance(parsed, dict) else {}
    return {}


def _secret_ref_payload(secret_ref_id: str, hint: str | None) -> dict[str, object]:
    return {
        "_secret_ref": secret_ref_id,
        "_redacted": True,
        "hint": hint or "***",
    }


async def _ensure_default_workspace(conn: AsyncConnection) -> str:
    result = await conn.execute(
        text(
            """
            SELECT id
            FROM workspaces
            WHERE is_default = 1 OR slug = 'default'
            ORDER BY is_default DESC, created_at ASC
            LIMIT 1
            """
        )
    )
    workspace_id = result.scalar_one_or_none()
    if workspace_id:
        return str(workspace_id)

    workspace_id = str(uuid.uuid4())
    now = utc_now()
    await conn.execute(
        text(
            """
            INSERT INTO workspaces (
                id,
                name,
                slug,
                description,
                is_default,
                is_active,
                created_at,
                updated_at
            )
            VALUES (
                :id,
                :name,
                :slug,
                :description,
                :is_default,
                :is_active,
                :created_at,
                :updated_at
            )
            """
        ),
        {
            "id": workspace_id,
            "name": "Default Workspace",
            "slug": "default",
            "description": "Default operational workspace for Truthound Dashboard",
            "is_default": True,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
    )
    logger.info("Migration: Created default workspace %s", workspace_id)
    return workspace_id


async def _workspace_ids(conn: AsyncConnection) -> list[str]:
    if not await _table_exists(conn, "workspaces"):
        return []
    result = await conn.execute(text("SELECT id FROM workspaces ORDER BY created_at ASC"))
    return [str(row[0]) for row in result.fetchall()]


async def _ensure_default_queue(conn: AsyncConnection, workspace_id: str) -> str:
    result = await conn.execute(
        text(
            """
            SELECT id
            FROM incident_queues
            WHERE workspace_id = :workspace_id AND (is_default = 1 OR slug = 'unassigned')
            ORDER BY is_default DESC, created_at ASC
            LIMIT 1
            """
        ),
        {"workspace_id": workspace_id},
    )
    queue_id = result.scalar_one_or_none()
    if queue_id:
        return str(queue_id)

    queue_id = str(uuid.uuid4())
    now = utc_now()
    await conn.execute(
        text(
            """
            INSERT INTO incident_queues (
                id,
                workspace_id,
                name,
                slug,
                description,
                is_default,
                is_active,
                routing_metadata,
                created_at,
                updated_at
            )
            VALUES (
                :id,
                :workspace_id,
                :name,
                :slug,
                :description,
                :is_default,
                :is_active,
                :routing_metadata,
                :created_at,
                :updated_at
            )
            """
        ),
        {
            "id": queue_id,
            "workspace_id": workspace_id,
            "name": "Unassigned",
            "slug": "unassigned",
            "description": "Default holding queue for new incidents",
            "is_default": True,
            "is_active": True,
            "routing_metadata": _json_value({"routing": "default"}),
            "created_at": now,
            "updated_at": now,
        },
    )
    logger.info("Migration: Created default incident queue %s for workspace %s", queue_id, workspace_id)
    return queue_id


async def _maybe_rebuild_generated_reports(conn: AsyncConnection) -> None:
    if not await _table_exists(conn, "generated_reports"):
        return
    report_columns = await _list_columns(conn, "generated_reports")
    if "reporter_id" not in report_columns:
        return

    await conn.execute(text("ALTER TABLE generated_reports RENAME TO generated_reports_legacy"))
    await conn.execute(
        text(
            """
            CREATE TABLE generated_reports (
                validation_id VARCHAR(36),
                workspace_id VARCHAR(36),
                source_id VARCHAR(36),
                id VARCHAR(36) NOT NULL,
                name VARCHAR(255) NOT NULL,
                artifact_type VARCHAR(50) NOT NULL DEFAULT 'report',
                description TEXT,
                format VARCHAR(20) NOT NULL,
                theme VARCHAR(50),
                locale VARCHAR(10) NOT NULL DEFAULT 'en',
                status VARCHAR(20) NOT NULL,
                file_path VARCHAR(500),
                file_size INTEGER,
                content_hash VARCHAR(64),
                config JSON,
                metadata JSON,
                error_message TEXT,
                generation_time_ms FLOAT,
                expires_at DATETIME,
                downloaded_count INTEGER NOT NULL DEFAULT 0,
                last_downloaded_at DATETIME,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(validation_id) REFERENCES validations (id) ON DELETE SET NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE SET NULL,
                FOREIGN KEY(source_id) REFERENCES sources (id) ON DELETE SET NULL
            )
            """
        )
    )
    await conn.execute(
        text(
            """
            INSERT INTO generated_reports (
                validation_id,
                workspace_id,
                source_id,
                id,
                name,
                artifact_type,
                description,
                format,
                theme,
                locale,
                status,
                file_path,
                file_size,
                content_hash,
                config,
                metadata,
                error_message,
                generation_time_ms,
                expires_at,
                downloaded_count,
                last_downloaded_at,
                created_at,
                updated_at
            )
            SELECT
                validation_id,
                workspace_id,
                source_id,
                id,
                name,
                COALESCE(artifact_type, 'report'),
                description,
                format,
                theme,
                locale,
                status,
                file_path,
                file_size,
                content_hash,
                config,
                metadata,
                error_message,
                generation_time_ms,
                expires_at,
                downloaded_count,
                last_downloaded_at,
                created_at,
                updated_at
            FROM generated_reports_legacy
            """
        )
    )
    await conn.execute(text("DROP TABLE generated_reports_legacy"))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_generated_reports_validation ON generated_reports (validation_id)"))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_generated_reports_workspace ON generated_reports (workspace_id)"))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_generated_reports_source ON generated_reports (source_id)"))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_generated_reports_artifact_type ON generated_reports (artifact_type)"))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_generated_reports_status ON generated_reports (status)"))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_generated_reports_format ON generated_reports (format)"))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_generated_reports_created ON generated_reports (created_at)"))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_generated_reports_expires ON generated_reports (expires_at)"))
    logger.info("Migration: Rebuilt generated_reports without reporter_id")


async def _migration_legacy_backfills_and_cleanup(conn: AsyncConnection) -> None:
    migrations = [
        ("schedules", "trigger_type", "VARCHAR(50)", "cron"),
        ("schedules", "trigger_config", "JSON", None),
        ("schedules", "trigger_count", "INTEGER", 0),
        ("schedules", "last_trigger_result", "JSON", None),
        ("sources", "workspace_id", "VARCHAR(36)", None),
        ("sources", "environment", "VARCHAR(32)", "production"),
        ("sources", "config_version", "INTEGER", 1),
        ("sources", "credential_updated_at", "DATETIME", None),
        ("notification_channels", "config_version", "INTEGER", 1),
        ("notification_channels", "credential_updated_at", "DATETIME", None),
        ("generated_reports", "workspace_id", "VARCHAR(36)", None),
        ("generated_reports", "artifact_type", "VARCHAR(50)", "report"),
        ("routing_rules", "workspace_id", "VARCHAR(36)", None),
        ("deduplication_configs", "workspace_id", "VARCHAR(36)", None),
        ("throttling_configs", "workspace_id", "VARCHAR(36)", None),
        ("escalation_policies", "workspace_id", "VARCHAR(36)", None),
        ("escalation_incidents", "workspace_id", "VARCHAR(36)", None),
        ("escalation_incidents", "queue_id", "VARCHAR(36)", None),
        ("escalation_incidents", "assignee_user_id", "VARCHAR(36)", None),
        ("escalation_incidents", "assigned_by", "VARCHAR(36)", None),
        ("escalation_incidents", "assigned_at", "DATETIME", None),
    ]
    legacy_tables = [
        "activities",
        "asset_columns",
        "asset_tags",
        "catalog_assets",
        "comments",
        "cross_alert_configs",
        "cross_alert_correlations",
        "cross_alert_trigger_events",
        "custom_reporters",
        "custom_validators",
        "drift_alerts",
        "drift_monitor_runs",
        "drift_monitors",
        "glossary_categories",
        "glossary_terms",
        "model_alert_handlers",
        "model_alert_rules",
        "model_alerts",
        "model_metrics",
        "model_predictions",
        "monitored_models",
        "plugin_execution_logs",
        "plugin_hooks",
        "plugin_ratings",
        "plugin_signatures",
        "security_policies",
        "schema_watcher_alerts",
        "schema_watcher_runs",
        "schema_watchers",
        "term_history",
        "term_relationships",
        "trusted_signers",
        "hot_reload_configs",
    ]

    for table_name, column_name, column_type, default in migrations:
        await _ensure_column(conn, table_name, column_name, column_type, default)

    await conn.execute(text("PRAGMA foreign_keys=OFF"))
    try:
        for table_name in legacy_tables:
            if await _table_exists(conn, table_name):
                await conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                logger.info("Migration: Dropped legacy table %s", table_name)

        await _maybe_rebuild_generated_reports(conn)
    finally:
        await conn.execute(text("PRAGMA foreign_keys=ON"))


def _parse_permission_keys(raw_permissions: object) -> list[str]:
    if raw_permissions is None:
        return []
    if isinstance(raw_permissions, str):
        try:
            parsed = json.loads(raw_permissions)
        except json.JSONDecodeError:
            return [raw_permissions] if raw_permissions else []
        return [str(item) for item in parsed if item]
    if isinstance(raw_permissions, list):
        return [str(item) for item in raw_permissions if item]
    return []


async def _migration_normalize_rbac(conn: AsyncConnection) -> None:
    if not await _table_exists(conn, "roles"):
        return
    if not await _table_exists(conn, "permissions") or not await _table_exists(conn, "role_permissions"):
        return
    if "permissions" not in await _list_columns(conn, "roles"):
        return

    role_rows = await conn.execute(text("SELECT id, name, permissions FROM roles"))
    for role_id, role_name, raw_permissions in role_rows.fetchall():
        permission_keys = sorted(set(_parse_permission_keys(raw_permissions)))
        if not permission_keys:
            continue

        for key in permission_keys:
            category = key.split(":", 1)[0]
            permission_row = await conn.execute(
                text("SELECT id FROM permissions WHERE key = :key"),
                {"key": key},
            )
            permission_id = permission_row.scalar_one_or_none()
            if permission_id is None:
                permission_id = str(uuid.uuid4())
                now = utc_now()
                await conn.execute(
                    text(
                        """
                        INSERT INTO permissions (
                            id,
                            key,
                            category,
                            description,
                            is_system,
                            created_at,
                            updated_at
                        )
                        VALUES (
                            :id,
                            :key,
                            :category,
                            :description,
                            :is_system,
                            :created_at,
                            :updated_at
                        )
                        """
                    ),
                    {
                        "id": permission_id,
                        "key": key,
                        "category": category,
                        "description": f"{role_name.title()} permission for {key}",
                        "is_system": True,
                        "created_at": now,
                        "updated_at": now,
                    },
                )

            exists = await conn.execute(
                text(
                    """
                    SELECT 1
                    FROM role_permissions
                    WHERE role_id = :role_id AND permission_id = :permission_id
                    """
                ),
                {"role_id": role_id, "permission_id": permission_id},
            )
            if exists.scalar_one_or_none() is None:
                now = utc_now()
                await conn.execute(
                    text(
                        """
                        INSERT INTO role_permissions (
                            id,
                            role_id,
                            permission_id,
                            created_at,
                            updated_at
                        )
                        VALUES (
                            :id,
                            :role_id,
                            :permission_id,
                            :created_at,
                            :updated_at
                        )
                        """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "role_id": role_id,
                        "permission_id": permission_id,
                        "created_at": now,
                        "updated_at": now,
                    },
                )


async def _upsert_secret_ref(
    conn: AsyncConnection,
    *,
    workspace_id: str,
    name: str,
    kind: str,
    raw_value: str,
    created_at: datetime,
    updated_at: datetime,
) -> str:
    existing = await conn.execute(
        text(
            """
            SELECT id
            FROM secret_refs
            WHERE workspace_id = :workspace_id AND name = :name
            """
        ),
        {"workspace_id": workspace_id, "name": name},
    )
    secret_ref_id = existing.scalar_one_or_none()
    payload = {
        "workspace_id": workspace_id,
        "name": name,
        "kind": kind,
        "encrypted_value": encrypt_value(raw_value),
        "redacted_hint": mask_sensitive_value(raw_value),
        "metadata": _json_value({"field": name.rsplit(":", 1)[-1]}),
        "rotated_at": updated_at,
        "updated_at": updated_at,
    }
    if secret_ref_id is not None:
        await conn.execute(
            text(
                """
                UPDATE secret_refs
                SET
                    provider = 'local-db',
                    kind = :kind,
                    encrypted_value = :encrypted_value,
                    redacted_hint = :redacted_hint,
                    metadata = :metadata,
                    rotated_at = :rotated_at,
                    updated_at = :updated_at
                WHERE id = :id
                """
            ),
            {
                "id": secret_ref_id,
                **payload,
            },
        )
        return str(secret_ref_id)

    secret_ref_id = str(uuid.uuid4())
    await conn.execute(
        text(
            """
            INSERT INTO secret_refs (
                id,
                workspace_id,
                provider,
                name,
                kind,
                encrypted_value,
                redacted_hint,
                metadata,
                created_by,
                rotated_at,
                created_at,
                updated_at
            )
            VALUES (
                :id,
                :workspace_id,
                'local-db',
                :name,
                :kind,
                :encrypted_value,
                :redacted_hint,
                :metadata,
                NULL,
                :rotated_at,
                :created_at,
                :updated_at
            )
            """
        ),
        {
            "id": secret_ref_id,
            "created_at": created_at,
            **payload,
        },
    )
    return secret_ref_id


def _notification_channel_secret_fields(channel_type: str | None) -> set[str]:
    secret_fields_by_type = {
        "slack": {"webhook_url"},
        "email": {"smtp_password", "api_key"},
        "discord": {"webhook_url"},
        "teams": {"webhook_url"},
        "telegram": {"bot_token"},
        "pagerduty": {"routing_key"},
        "opsgenie": {"api_key"},
        "github": {"token"},
    }
    return secret_fields_by_type.get((channel_type or "").lower(), set())


async def _persist_secret_refs_in_config(
    conn: AsyncConnection,
    *,
    config: dict[str, object],
    workspace_id: str,
    name_prefix: str,
    kind: str,
    created_at: datetime,
    updated_at: datetime,
    secret_fields: set[str] | None = None,
) -> dict[str, object]:
    persisted: dict[str, object] = {}
    explicit_secret_fields = secret_fields or set()
    for key, value in config.items():
        secret_name = f"{name_prefix}:{key}"
        if isinstance(value, dict):
            if isinstance(value.get("_secret_ref"), str):
                persisted[key] = value
            elif isinstance(value.get("_encrypted"), str):
                raw_value = decrypt_value(value["_encrypted"])
                secret_ref_id = await _upsert_secret_ref(
                    conn,
                    workspace_id=workspace_id,
                    name=secret_name,
                    kind=kind,
                    raw_value=raw_value,
                    created_at=created_at,
                    updated_at=updated_at,
                )
                persisted[key] = _secret_ref_payload(secret_ref_id, mask_sensitive_value(raw_value))
            else:
                persisted[key] = await _persist_secret_refs_in_config(
                    conn,
                    config=value,
                    workspace_id=workspace_id,
                    name_prefix=secret_name,
                    kind=kind,
                    created_at=created_at,
                    updated_at=updated_at,
                    secret_fields=None,
                )
        elif isinstance(value, str) and value and (key in explicit_secret_fields or is_sensitive_field(key)):
            secret_ref_id = await _upsert_secret_ref(
                conn,
                workspace_id=workspace_id,
                name=secret_name,
                kind=kind,
                raw_value=value,
                created_at=created_at,
                updated_at=updated_at,
            )
            persisted[key] = _secret_ref_payload(secret_ref_id, mask_sensitive_value(value))
        else:
            persisted[key] = value
    return persisted


async def _migration_secret_refs_and_ownership(conn: AsyncConnection) -> None:
    if await _table_exists(conn, "sources") and await _table_exists(conn, "secret_refs"):
        rows = await conn.execute(
            text(
                """
                SELECT
                    id,
                    name,
                    workspace_id,
                    config,
                    credential_updated_at,
                    created_at,
                    updated_at
                FROM sources
                """
            )
        )
        for row in rows.mappings().all():
            workspace_id = row["workspace_id"] or await _ensure_default_workspace(conn)
            created_at = row["created_at"] or utc_now()
            updated_at = row["updated_at"] or created_at
            config = _json_dict(row["config"])
            persisted_config = await _persist_secret_refs_in_config(
                conn,
                config=config,
                workspace_id=workspace_id,
                name_prefix=f"source:{row['id']}",
                kind="source",
                created_at=created_at,
                updated_at=updated_at,
                secret_fields=None,
            )
            await conn.execute(
                text(
                    """
                    UPDATE sources
                    SET
                        workspace_id = :workspace_id,
                        config = :config,
                        credential_updated_at = COALESCE(credential_updated_at, :credential_updated_at)
                    WHERE id = :id
                    """
                ),
                {
                    "id": row["id"],
                    "workspace_id": workspace_id,
                    "config": _json_value(persisted_config),
                    "credential_updated_at": row["credential_updated_at"] or updated_at,
                },
            )

    if await _table_exists(conn, "sources") and await _table_exists(conn, "source_ownerships"):
        source_rows = await conn.execute(
            text("SELECT id, workspace_id, created_at, updated_at FROM sources")
        )
        for row in source_rows.mappings().all():
            exists = await conn.execute(
                text("SELECT 1 FROM source_ownerships WHERE source_id = :source_id"),
                {"source_id": row["id"]},
            )
            if exists.scalar_one_or_none() is not None:
                continue
            await conn.execute(
                text(
                    """
                    INSERT INTO source_ownerships (
                        id,
                        source_id,
                        workspace_id,
                        owner_user_id,
                        team_id,
                        domain_id,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        :id,
                        :source_id,
                        :workspace_id,
                        NULL,
                        NULL,
                        NULL,
                        :created_at,
                        :updated_at
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "source_id": row["id"],
                    "workspace_id": row["workspace_id"] or await _ensure_default_workspace(conn),
                    "created_at": row["created_at"] or utc_now(),
                    "updated_at": row["updated_at"] or utc_now(),
                },
            )


async def _migration_notification_channel_secrets(conn: AsyncConnection) -> None:
    if not await _table_exists(conn, "notification_channels"):
        return
    if not await _table_exists(conn, "secret_refs"):
        return

    default_workspace_id = await _ensure_default_workspace(conn)
    rows = await conn.execute(
        text(
            """
            SELECT
                id,
                type,
                config,
                config_version,
                credential_updated_at,
                created_at,
                updated_at
            FROM notification_channels
            """
        )
    )
    for row in rows.mappings().all():
        created_at = row["created_at"] or utc_now()
        updated_at = row["updated_at"] or created_at
        config = _json_dict(row["config"])
        persisted_config = await _persist_secret_refs_in_config(
            conn,
            config=config,
            workspace_id=default_workspace_id,
            name_prefix=f"notification-channel:{row['id']}",
            kind="notification_channel",
            created_at=created_at,
            updated_at=updated_at,
            secret_fields=_notification_channel_secret_fields(row["type"]),
        )
        credential_updated_at = row["credential_updated_at"]
        if credential_updated_at is None and persisted_config != config:
            credential_updated_at = updated_at

        await conn.execute(
            text(
                """
                UPDATE notification_channels
                SET
                    config = :config,
                    config_version = COALESCE(config_version, 1),
                    credential_updated_at = :credential_updated_at
                WHERE id = :id
                """
            ),
            {
                "id": row["id"],
                "config": _json_value(persisted_config),
                "credential_updated_at": credential_updated_at,
            },
        )

    logger.info("Migration: Backfilled notification channel secrets into secret_refs")


async def _rebuild_roles_without_permissions_column(conn: AsyncConnection) -> None:
    if not await _table_exists(conn, "roles"):
        return
    if "permissions" not in await _list_columns(conn, "roles"):
        return

    await conn.execute(text("ALTER TABLE roles RENAME TO roles_legacy"))
    await conn.execute(
        text(
            """
            CREATE TABLE roles (
                id VARCHAR(36) NOT NULL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                is_system BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
            """
        )
    )
    await conn.execute(
        text(
            """
            INSERT INTO roles (id, name, description, is_system, created_at, updated_at)
            SELECT id, name, description, is_system, created_at, updated_at
            FROM roles_legacy
            """
        )
    )
    await conn.execute(text("DROP TABLE roles_legacy"))
    await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_roles_name ON roles (name)"))


async def _migration_cutover_cleanup(conn: AsyncConnection) -> None:
    await conn.execute(text("PRAGMA foreign_keys=OFF"))
    try:
        await _rebuild_roles_without_permissions_column(conn)
        if await _table_exists(conn, "generated_reports"):
            await conn.execute(text("DROP TABLE generated_reports"))
            logger.info("Migration: Dropped legacy generated_reports table")
    finally:
        await conn.execute(text("PRAGMA foreign_keys=ON"))


async def _migration_artifact_records(conn: AsyncConnection) -> None:
    if not await _table_exists(conn, "artifact_records"):
        return
    if not await _table_exists(conn, "generated_reports"):
        return

    rows = await conn.execute(
        text(
            """
            SELECT
                id,
                validation_id,
                workspace_id,
                source_id,
                name,
                artifact_type,
                description,
                format,
                theme,
                locale,
                status,
                file_path,
                file_size,
                content_hash,
                metadata,
                error_message,
                generation_time_ms,
                expires_at,
                downloaded_count,
                last_downloaded_at,
                created_at,
                updated_at
            FROM generated_reports
            """
        )
    )

    for row in rows.mappings().all():
        exists = await conn.execute(
            text("SELECT 1 FROM artifact_records WHERE id = :id"),
            {"id": row["id"]},
        )
        if exists.scalar_one_or_none() is not None:
            continue

        await conn.execute(
            text(
                """
                INSERT INTO artifact_records (
                    id,
                    workspace_id,
                    source_id,
                    validation_id,
                    artifact_type,
                    format,
                    status,
                    title,
                    description,
                    file_path,
                    external_url,
                    file_size,
                    content_hash,
                    metadata,
                    error_message,
                    generation_time_ms,
                    expires_at,
                    downloaded_count,
                    last_downloaded_at,
                    locale,
                    theme,
                    created_at,
                    updated_at
                )
                VALUES (
                    :id,
                    :workspace_id,
                    :source_id,
                    :validation_id,
                    :artifact_type,
                    :format,
                    :status,
                    :title,
                    :description,
                    :file_path,
                    :external_url,
                    :file_size,
                    :content_hash,
                    :metadata,
                    :error_message,
                    :generation_time_ms,
                    :expires_at,
                    :downloaded_count,
                    :last_downloaded_at,
                    :locale,
                    :theme,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "id": row["id"],
                "workspace_id": row["workspace_id"],
                "source_id": row["source_id"],
                "validation_id": row["validation_id"],
                "artifact_type": row["artifact_type"] or "report",
                "format": row["format"] or "html",
                "status": row["status"] or "pending",
                "title": row["name"],
                "description": row["description"],
                "file_path": row["file_path"],
                "external_url": None,
                "file_size": row["file_size"],
                "content_hash": row["content_hash"],
                "metadata": _json_value(row["metadata"]),
                "error_message": row["error_message"],
                "generation_time_ms": row["generation_time_ms"],
                "expires_at": row["expires_at"],
                "downloaded_count": row["downloaded_count"] or 0,
                "last_downloaded_at": row["last_downloaded_at"],
                "locale": row["locale"] or "en",
                "theme": row["theme"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            },
        )

    logger.info("Migration: Backfilled artifact_records from generated_reports")


async def _migration_workspace_scope_and_queues(conn: AsyncConnection) -> None:
    default_workspace_id = await _ensure_default_workspace(conn)

    workspace_scoped_tables = [
        "sources",
        "routing_rules",
        "deduplication_configs",
        "throttling_configs",
        "escalation_policies",
        "escalation_incidents",
    ]
    for table_name in workspace_scoped_tables:
        if await _table_exists(conn, table_name) and "workspace_id" in await _list_columns(conn, table_name):
            await conn.execute(
                text(
                    f"""
                    UPDATE {table_name}
                    SET workspace_id = :workspace_id
                    WHERE workspace_id IS NULL
                    """
                ),
                {"workspace_id": default_workspace_id},
            )

    for workspace_id in await _workspace_ids(conn):
        queue_id = await _ensure_default_queue(conn, workspace_id)
        if await _table_exists(conn, "escalation_incidents"):
            await conn.execute(
                text(
                    """
                    UPDATE escalation_incidents
                    SET queue_id = :queue_id
                    WHERE workspace_id = :workspace_id AND queue_id IS NULL
                    """
                ),
                {"workspace_id": workspace_id, "queue_id": queue_id},
            )


MIGRATIONS: list[tuple[str, str, MigrationFn]] = [
    (
        "20260322_001_legacy_backfills_and_cleanup",
        "Legacy backfills, workspace columns, and retired table cleanup",
        _migration_legacy_backfills_and_cleanup,
    ),
    (
        "20260322_002_normalize_rbac",
        "Normalize RBAC permissions into permissions and role_permissions tables",
        _migration_normalize_rbac,
    ),
    (
        "20260322_003_artifact_records",
        "Backfill canonical artifact_records from generated_reports",
        _migration_artifact_records,
    ),
    (
        "20260322_004_workspace_scope_and_queues",
        "Backfill workspace scope and default incident queues",
        _migration_workspace_scope_and_queues,
    ),
    (
        "20260322_005_secret_refs_and_ownership",
        "Backfill source secret_refs and normalized source ownership rows",
        _migration_secret_refs_and_ownership,
    ),
    (
        "20260322_005b_notification_channel_secrets",
        "Backfill notification channel secrets into secret_refs",
        _migration_notification_channel_secrets,
    ),
    (
        "20260322_006_cutover_cleanup",
        "Drop legacy generated_reports and remove roles.permissions legacy column",
        _migration_cutover_cleanup,
    ),
]


async def _run_migrations(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        applied = await _applied_migrations(conn)

    for version, description, migration in MIGRATIONS:
        if version in applied:
            continue
        async with engine.begin() as conn:
            logger.info("Running migration %s: %s", version, description)
            await _ensure_schema_migrations_table(conn)
            await migration(conn)
            await _record_migration(conn, version=version, description=description)


async def init_db(engine: AsyncEngine | None = None) -> None:
    target_engine = engine or get_engine()
    async with target_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await _run_migrations(target_engine)


async def drop_db(engine: AsyncEngine | None = None) -> None:
    target_engine = engine or get_engine()
    async with target_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def reset_db(engine: AsyncEngine | None = None) -> None:
    await drop_db(engine)
    await init_db(engine)


def reset_connection() -> None:
    global _engine, _session_factory
    _engine = None
    _session_factory = None
