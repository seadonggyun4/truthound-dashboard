"""Shared source input helpers for domain services."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db import Source, get_session

from ..datasource_factory import SourceType, create_datasource
from ..encryption import decrypt_config, is_sensitive_field
from ..secrets import LocalEncryptedDbSecretProvider
from ..truthound_adapter import DataInput

logger = logging.getLogger(__name__)


def _has_sensitive_config(config: dict[str, Any]) -> bool:
    for key, value in config.items():
        if isinstance(value, dict) and _has_sensitive_config(value):
            return True
        if isinstance(value, str) and value and is_sensitive_field(key):
            return True
    return False


async def _resolve_source_config(
    source: Source,
    session: AsyncSession | None = None,
) -> dict[str, Any]:
    config = source.config or {}
    if session is None:
        return decrypt_config(config)
    provider = LocalEncryptedDbSecretProvider(session)
    return await provider.materialize_config(decrypt_config(config))


async def get_data_input_from_source(
    source: Source,
    session: AsyncSession | None = None,
) -> DataInput:
    source_type = source.type.lower()
    config = await _resolve_source_config(source, session)

    if SourceType.is_file_type(source_type):
        path = config.get("path") or source.source_path
        if not path:
            raise ValueError(f"No path configured for file source: {source.name}")
        return path

    try:
        full_config = {"type": source_type, **config}
        return create_datasource(full_config)
    except Exception as exc:
        logger.error("Failed to create DataSource for %s: %s", source.name, exc)
        raise ValueError(f"Failed to create DataSource: {exc}") from exc


async def get_async_data_input_from_source(
    source: Source,
    session: AsyncSession | None = None,
) -> DataInput:
    from ..datasource_factory import create_datasource_async

    source_type = source.type.lower()
    config = await _resolve_source_config(source, session)

    if not SourceType.is_async_type(source_type):
        raise ValueError(f"Source type '{source_type}' doesn't require async creation")

    try:
        full_config = {"type": source_type, **config}
        return await create_datasource_async(full_config)
    except Exception as exc:
        logger.error("Failed to create async DataSource for %s: %s", source.name, exc)
        raise ValueError(f"Failed to create async DataSource: {exc}") from exc


async def get_source_data_input(source_id: str) -> object:
    """Resolve a source ID into a Truthound data input using a fresh DB session."""

    async with get_session() as session:
        result = await session.execute(select(Source).where(Source.id == source_id))
        source = result.scalar_one_or_none()
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")
        if source.type and source.type.lower() in {"mongodb", "elasticsearch", "kafka"}:
            return await get_async_data_input_from_source(source, session)
        return await get_data_input_from_source(source, session)


__all__ = [
    "_has_sensitive_config",
    "_resolve_source_config",
    "get_async_data_input_from_source",
    "get_data_input_from_source",
    "get_source_data_input",
]
