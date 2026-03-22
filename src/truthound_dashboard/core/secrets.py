"""Secret reference storage and resolution for control-plane managed configs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db import SecretRef
from truthound_dashboard.time import utc_now

from .encryption import decrypt_value, encrypt_value, is_sensitive_field, mask_sensitive_value

SECRET_REF_KEY = "_secret_ref"
SECRET_REDACTED_KEY = "_redacted"
SECRET_HINT_KEY = "hint"


def is_secret_ref_payload(value: object) -> bool:
    return isinstance(value, dict) and isinstance(value.get(SECRET_REF_KEY), str)


def is_redacted_secret_payload(value: object) -> bool:
    return (
        isinstance(value, dict)
        and value.get(SECRET_REDACTED_KEY) is True
        and not is_secret_ref_payload(value)
    )


def get_secret_hint(value: object) -> str:
    if isinstance(value, dict) and isinstance(value.get(SECRET_HINT_KEY), str):
        return value[SECRET_HINT_KEY]
    return "***"


def build_secret_ref_payload(secret_ref: SecretRef) -> dict[str, Any]:
    return {
        SECRET_REF_KEY: secret_ref.id,
        SECRET_REDACTED_KEY: True,
        SECRET_HINT_KEY: secret_ref.redacted_hint or "***",
    }


def merge_secret_aware_configs(
    existing: dict[str, Any],
    incoming: dict[str, Any],
) -> dict[str, Any]:
    """Merge updates while preserving omitted secret placeholders."""

    merged: dict[str, Any] = dict(existing)
    for key, value in incoming.items():
        current = merged.get(key)
        if is_redacted_secret_payload(value) and (
            is_secret_ref_payload(current)
            or (isinstance(current, dict) and isinstance(current.get("_encrypted"), str))
        ):
            merged[key] = current
        elif isinstance(value, dict) and not is_secret_ref_payload(value) and not is_redacted_secret_payload(value):
            if isinstance(current, dict) and not is_secret_ref_payload(current):
                merged[key] = merge_secret_aware_configs(current, value)
            else:
                merged[key] = value
        else:
            merged[key] = value
    return merged


class SecretProvider(ABC):
    """Abstraction for persisted secret references."""

    @abstractmethod
    async def create_ref(
        self,
        *,
        workspace_id: str,
        name: str,
        kind: str,
        raw_value: str,
        created_by: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SecretRef:
        raise NotImplementedError

    @abstractmethod
    async def resolve(self, ref_id: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def rotate(self, ref_id: str, *, raw_value: str) -> SecretRef | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_ref(self, ref_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def materialize_config(self, config: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def persist_config(
        self,
        *,
        config: dict[str, Any],
        workspace_id: str,
        name_prefix: str,
        kind: str,
        created_by: str | None = None,
        secret_fields: set[str] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError


class LocalEncryptedDbSecretProvider(SecretProvider):
    """DB-backed secret refs encrypted with the local dashboard key."""

    provider_name = "local-db"

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_ref_by_name(self, *, workspace_id: str, name: str) -> SecretRef | None:
        result = await self.session.execute(
            select(SecretRef).where(
                SecretRef.workspace_id == workspace_id,
                SecretRef.name == name,
            )
        )
        return result.scalar_one_or_none()

    async def create_ref(
        self,
        *,
        workspace_id: str,
        name: str,
        kind: str,
        raw_value: str,
        created_by: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SecretRef:
        secret_ref = SecretRef(
            workspace_id=workspace_id,
            provider=self.provider_name,
            name=name,
            kind=kind,
            encrypted_value=encrypt_value(raw_value),
            redacted_hint=mask_sensitive_value(raw_value),
            secret_metadata=metadata or {},
            created_by=created_by,
            rotated_at=utc_now(),
        )
        self.session.add(secret_ref)
        await self.session.flush()
        await self.session.refresh(secret_ref)
        return secret_ref

    async def resolve(self, ref_id: str) -> str | None:
        result = await self.session.execute(
            select(SecretRef).where(SecretRef.id == ref_id)
        )
        secret_ref = result.scalar_one_or_none()
        if secret_ref is None:
            return None
        return decrypt_value(secret_ref.encrypted_value)

    async def rotate(self, ref_id: str, *, raw_value: str) -> SecretRef | None:
        result = await self.session.execute(
            select(SecretRef).where(SecretRef.id == ref_id)
        )
        secret_ref = result.scalar_one_or_none()
        if secret_ref is None:
            return None
        secret_ref.encrypted_value = encrypt_value(raw_value)
        secret_ref.redacted_hint = mask_sensitive_value(raw_value)
        secret_ref.rotated_at = utc_now()
        await self.session.flush()
        await self.session.refresh(secret_ref)
        return secret_ref

    async def delete_ref(self, ref_id: str) -> None:
        result = await self.session.execute(
            select(SecretRef).where(SecretRef.id == ref_id)
        )
        secret_ref = result.scalar_one_or_none()
        if secret_ref is not None:
            await self.session.delete(secret_ref)

    async def upsert_ref(
        self,
        *,
        workspace_id: str,
        name: str,
        kind: str,
        raw_value: str,
        created_by: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SecretRef:
        existing_ref = await self._get_ref_by_name(workspace_id=workspace_id, name=name)
        if existing_ref is None:
            return await self.create_ref(
                workspace_id=workspace_id,
                name=name,
                kind=kind,
                raw_value=raw_value,
                created_by=created_by,
                metadata=metadata,
            )

        existing_ref.kind = kind
        existing_ref.encrypted_value = encrypt_value(raw_value)
        existing_ref.redacted_hint = mask_sensitive_value(raw_value)
        existing_ref.secret_metadata = metadata or {}
        existing_ref.rotated_at = utc_now()
        if created_by is not None:
            existing_ref.created_by = created_by
        await self.session.flush()
        await self.session.refresh(existing_ref)
        return existing_ref

    async def materialize_config(self, config: dict[str, Any]) -> dict[str, Any]:
        materialized: dict[str, Any] = {}
        for key, value in config.items():
            if is_secret_ref_payload(value):
                secret_value = await self.resolve(value[SECRET_REF_KEY])
                materialized[key] = secret_value
            elif isinstance(value, dict) and isinstance(value.get("_encrypted"), str):
                materialized[key] = decrypt_value(value["_encrypted"])
            elif isinstance(value, dict):
                materialized[key] = await self.materialize_config(value)
            else:
                materialized[key] = value
        return materialized

    async def persist_config(
        self,
        *,
        config: dict[str, Any],
        workspace_id: str,
        name_prefix: str,
        kind: str,
        created_by: str | None = None,
        secret_fields: set[str] | None = None,
    ) -> dict[str, Any]:
        persisted: dict[str, Any] = {}
        explicit_secret_fields = secret_fields or set()
        for key, value in config.items():
            secret_name = f"{name_prefix}:{key}"
            if is_secret_ref_payload(value):
                persisted[key] = value
            elif is_redacted_secret_payload(value):
                persisted[key] = value
            elif isinstance(value, dict) and isinstance(value.get("_encrypted"), str):
                secret_ref = await self.upsert_ref(
                    workspace_id=workspace_id,
                    name=secret_name,
                    kind=kind,
                    raw_value=decrypt_value(value["_encrypted"]),
                    created_by=created_by,
                    metadata={"field": key},
                )
                persisted[key] = build_secret_ref_payload(secret_ref)
            elif isinstance(value, dict) and key not in explicit_secret_fields and not is_sensitive_field(key):
                persisted[key] = await self.persist_config(
                    config=value,
                    workspace_id=workspace_id,
                    name_prefix=secret_name,
                    kind=kind,
                    created_by=created_by,
                    secret_fields=None,
                )
            elif isinstance(value, str) and value and (
                key in explicit_secret_fields or is_sensitive_field(key)
            ):
                secret_ref = await self.upsert_ref(
                    workspace_id=workspace_id,
                    name=secret_name,
                    kind=kind,
                    raw_value=value,
                    created_by=created_by,
                    metadata={"field": key},
                )
                persisted[key] = build_secret_ref_payload(secret_ref)
            else:
                persisted[key] = value
        return persisted
