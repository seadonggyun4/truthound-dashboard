"""Notification service layer for business logic.

This module provides the service layer for managing notification
channels, rules, and logs using the repository pattern.

Services:
    - NotificationChannelService: Manage notification channels
    - NotificationRuleService: Manage notification rules
    - NotificationLogService: Query notification logs
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db import (
    BaseRepository,
    NotificationChannel,
    NotificationLog,
    NotificationRule,
    Workspace,
)
from truthound_dashboard.time import utc_now

from .base import ChannelRegistry
from ..secrets import (
    LocalEncryptedDbSecretProvider,
    is_redacted_secret_payload,
    is_secret_ref_payload,
    merge_secret_aware_configs,
)
from ..encryption import is_sensitive_field
from .serialization import get_channel_secret_fields, normalize_channel_config


# =============================================================================
# Repositories
# =============================================================================


class NotificationChannelRepository(BaseRepository[NotificationChannel]):
    """Repository for NotificationChannel operations."""

    model = NotificationChannel

    async def get_active(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[NotificationChannel]:
        """Get active channels only.

        Args:
            offset: Number to skip.
            limit: Maximum to return.

        Returns:
            Sequence of active channels.
        """
        return await self.list(
            offset=offset,
            limit=limit,
            filters=[NotificationChannel.is_active == True],
        )

    async def get_by_type(
        self,
        channel_type: str,
        *,
        active_only: bool = True,
    ) -> Sequence[NotificationChannel]:
        """Get channels by type.

        Args:
            channel_type: Type of channels to get.
            active_only: Only return active channels.

        Returns:
            Sequence of channels.
        """
        filters = [NotificationChannel.type == channel_type]
        if active_only:
            filters.append(NotificationChannel.is_active == True)

        return await self.list(filters=filters)


class NotificationRuleRepository(BaseRepository[NotificationRule]):
    """Repository for NotificationRule operations."""

    model = NotificationRule

    async def get_active(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[NotificationRule]:
        """Get active rules only.

        Args:
            offset: Number to skip.
            limit: Maximum to return.

        Returns:
            Sequence of active rules.
        """
        return await self.list(
            offset=offset,
            limit=limit,
            filters=[NotificationRule.is_active == True],
        )

    async def get_by_condition(
        self,
        condition: str,
        *,
        active_only: bool = True,
    ) -> Sequence[NotificationRule]:
        """Get rules by condition type.

        Args:
            condition: Condition type to filter by.
            active_only: Only return active rules.

        Returns:
            Sequence of rules.
        """
        filters = [NotificationRule.condition == condition]
        if active_only:
            filters.append(NotificationRule.is_active == True)

        return await self.list(filters=filters)

    async def get_for_source(
        self,
        source_id: str,
        *,
        active_only: bool = True,
    ) -> Sequence[NotificationRule]:
        """Get rules that apply to a specific source.

        Args:
            source_id: Source ID to check.
            active_only: Only return active rules.

        Returns:
            Sequence of rules.
        """
        # Get all active rules first, then filter by source
        filters = []
        if active_only:
            filters.append(NotificationRule.is_active == True)

        all_rules = await self.list(filters=filters if filters else None)

        # Filter to rules that match this source
        return [r for r in all_rules if r.matches_source(source_id)]


class NotificationLogRepository(BaseRepository[NotificationLog]):
    """Repository for NotificationLog operations."""

    model = NotificationLog

    async def get_for_channel(
        self,
        channel_id: str,
        *,
        limit: int = 50,
    ) -> Sequence[NotificationLog]:
        """Get logs for a specific channel.

        Args:
            channel_id: Channel ID.
            limit: Maximum to return.

        Returns:
            Sequence of logs.
        """
        return await self.list(
            limit=limit,
            filters=[NotificationLog.channel_id == channel_id],
            order_by=NotificationLog.created_at.desc(),
        )

    async def get_recent(
        self,
        *,
        hours: int = 24,
        limit: int = 100,
        status: str | None = None,
    ) -> Sequence[NotificationLog]:
        """Get recent notification logs.

        Args:
            hours: Number of hours to look back.
            limit: Maximum to return.
            status: Optional status filter.

        Returns:
            Sequence of logs.
        """
        cutoff = utc_now() - timedelta(hours=hours)
        filters = [NotificationLog.created_at >= cutoff]

        if status:
            filters.append(NotificationLog.status == status)

        return await self.list(
            limit=limit,
            filters=filters,
            order_by=NotificationLog.created_at.desc(),
        )

    async def get_stats(
        self,
        *,
        hours: int = 24,
    ) -> dict[str, Any]:
        """Get notification statistics.

        Args:
            hours: Number of hours to analyze.

        Returns:
            Statistics dictionary.
        """
        cutoff = utc_now() - timedelta(hours=hours)

        # Count by status
        result = await self.session.execute(
            select(
                NotificationLog.status,
                func.count(NotificationLog.id).label("count"),
            )
            .where(NotificationLog.created_at >= cutoff)
            .group_by(NotificationLog.status)
        )
        status_counts = {row.status: row.count for row in result}

        # Count by channel
        result = await self.session.execute(
            select(
                NotificationLog.channel_id,
                func.count(NotificationLog.id).label("count"),
            )
            .where(NotificationLog.created_at >= cutoff)
            .group_by(NotificationLog.channel_id)
        )
        channel_counts = {row.channel_id: row.count for row in result}

        return {
            "period_hours": hours,
            "total": sum(status_counts.values()),
            "by_status": status_counts,
            "by_channel": channel_counts,
            "success_rate": self._calculate_success_rate(status_counts),
        }

    def _calculate_success_rate(self, status_counts: dict[str, int]) -> float:
        """Calculate success rate from status counts."""
        total = sum(status_counts.values())
        if total == 0:
            return 100.0
        sent = status_counts.get("sent", 0)
        return round(sent / total * 100, 2)


# =============================================================================
# Services
# =============================================================================


class NotificationChannelService:
    """Service for managing notification channels.

    Provides business logic for channel CRUD operations
    and validation.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.repository = NotificationChannelRepository(session)
        self.secrets = LocalEncryptedDbSecretProvider(session)

    async def _get_secret_workspace_id(self) -> str:
        result = await self.session.execute(
            select(Workspace).order_by(Workspace.is_default.desc(), Workspace.created_at.asc()).limit(1)
        )
        workspace = result.scalar_one_or_none()
        if workspace is None:
            workspace = Workspace(
                name="Default Workspace",
                slug="default",
                description="Default operational workspace for notification secrets",
                is_default=True,
                is_active=True,
            )
            self.session.add(workspace)
            await self.session.flush()
            await self.session.refresh(workspace)
        return workspace.id

    async def _persist_channel_config(
        self,
        *,
        channel_id: str,
        channel_type: str,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        return await self.secrets.persist_config(
            config=config,
            workspace_id=await self._get_secret_workspace_id(),
            name_prefix=f"notification-channel:{channel_id}",
            kind="notification_channel",
            secret_fields=get_channel_secret_fields(channel_type),
        )

    async def _materialize_for_validation(
        self,
        *,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        return await self.secrets.materialize_config(config)

    async def _validate_config(
        self,
        *,
        channel_type: str,
        config: dict[str, Any],
    ) -> None:
        config = normalize_channel_config(channel_type, config)
        channel_class = ChannelRegistry.get(channel_type)
        if channel_class is None:
            available = ChannelRegistry.list_types()
            raise ValueError(
                f"Unknown channel type: {channel_type}. "
                f"Available types: {', '.join(available)}"
            )

        materialized = await self._materialize_for_validation(config=config)
        errors = channel_class.validate_config(materialized)
        if errors:
            raise ValueError(f"Invalid configuration: {'; '.join(errors)}")

    def _contains_secret_update(
        self,
        *,
        channel_type: str,
        config: dict[str, Any],
    ) -> bool:
        secret_fields = get_channel_secret_fields(channel_type)
        for key, value in config.items():
            if is_secret_ref_payload(value) or is_redacted_secret_payload(value):
                continue
            if (key in secret_fields or is_sensitive_field(key)) and isinstance(value, str) and value:
                return True
            if (
                (key in secret_fields or is_sensitive_field(key))
                and isinstance(value, dict)
                and isinstance(value.get("_encrypted"), str)
            ):
                return True
            if (
                isinstance(value, dict)
                and not is_secret_ref_payload(value)
                and not is_redacted_secret_payload(value)
                and self._contains_secret_update(channel_type=channel_type, config=value)
            ):
                return True
        return False

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        active_only: bool = False,
        channel_type: str | None = None,
    ) -> Sequence[NotificationChannel]:
        """List notification channels.

        Args:
            offset: Number to skip.
            limit: Maximum to return.
            active_only: Only return active channels.
            channel_type: Optional type filter.

        Returns:
            Sequence of channels.
        """
        if channel_type:
            channels = await self.repository.get_by_type(
                channel_type, active_only=active_only
            )
            return channels[offset : offset + limit]

        if active_only:
            return await self.repository.get_active(offset=offset, limit=limit)

        return await self.repository.list(offset=offset, limit=limit)

    async def get_by_id(self, channel_id: str) -> NotificationChannel | None:
        """Get channel by ID.

        Args:
            channel_id: Channel ID.

        Returns:
            Channel or None.
        """
        return await self.repository.get_by_id(channel_id)

    async def create(
        self,
        *,
        name: str,
        channel_type: str,
        config: dict[str, Any],
        is_active: bool = True,
    ) -> NotificationChannel:
        """Create a new notification channel.

        Args:
            name: Channel name.
            channel_type: Channel type (slack, email, webhook).
            config: Channel configuration.
            is_active: Whether channel is active.

        Returns:
            Created channel.

        Raises:
            ValueError: If channel type is unknown or config is invalid.
        """
        normalized_config = normalize_channel_config(channel_type, config)
        await self._validate_config(channel_type=channel_type, config=normalized_config)

        channel = await self.repository.create(
            name=name,
            type=channel_type,
            config={},
            config_version=1,
            credential_updated_at=utc_now() if self._contains_secret_update(channel_type=channel_type, config=normalized_config) else None,
            is_active=is_active,
        )
        channel.config = await self._persist_channel_config(
            channel_id=channel.id,
            channel_type=channel_type,
            config=normalized_config,
        )
        await self.session.flush()
        await self.session.refresh(channel)
        return channel

    async def update(
        self,
        channel_id: str,
        *,
        name: str | None = None,
        config: dict[str, Any] | None = None,
        is_active: bool | None = None,
    ) -> NotificationChannel | None:
        """Update a notification channel.

        Args:
            channel_id: Channel ID.
            name: New name.
            config: New configuration.
            is_active: New active status.

        Returns:
            Updated channel or None if not found.

        Raises:
            ValueError: If config is invalid.
        """
        channel = await self.repository.get_by_id(channel_id)
        if channel is None:
            return None

        config_changed = False
        secret_changed = False

        # Validate config if provided
        if config is not None:
            merged_config = merge_secret_aware_configs(channel.config or {}, config)
            merged_config = normalize_channel_config(channel.type, merged_config)
            await self._validate_config(channel_type=channel.type, config=merged_config)
            config = merged_config
            config_changed = True
            secret_changed = self._contains_secret_update(
                channel_type=channel.type,
                config=config,
            )

        # Update fields
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if config is not None:
            update_data["config"] = await self._persist_channel_config(
                channel_id=channel.id,
                channel_type=channel.type,
                config=config,
            )
        if is_active is not None:
            update_data["is_active"] = is_active
        if config_changed:
            update_data["config_version"] = (channel.config_version or 0) + 1
        if secret_changed:
            update_data["credential_updated_at"] = utc_now()

        if not update_data:
            return channel

        return await self.repository.update(channel_id, **update_data)

    async def rotate_credentials(
        self,
        channel_id: str,
        *,
        config: dict[str, Any],
    ) -> NotificationChannel | None:
        channel = await self.repository.get_by_id(channel_id)
        if channel is None:
            return None

        secret_fields = get_channel_secret_fields(channel.type)
        requested_secret_fields = {
            key for key, value in config.items()
            if key in secret_fields and value not in (None, "")
        }
        if not requested_secret_fields:
            raise ValueError("No secret-bearing fields provided for credential rotation")

        merged_config = merge_secret_aware_configs(channel.config or {}, config)
        merged_config = normalize_channel_config(channel.type, merged_config)
        await self._validate_config(channel_type=channel.type, config=merged_config)
        persisted_config = await self._persist_channel_config(
            channel_id=channel.id,
            channel_type=channel.type,
            config=merged_config,
        )
        return await self.repository.update(
            channel_id,
            config=persisted_config,
            config_version=(channel.config_version or 0) + 1,
            credential_updated_at=utc_now(),
        )

    async def delete(self, channel_id: str) -> bool:
        """Delete a notification channel.

        Args:
            channel_id: Channel ID.

        Returns:
            True if deleted.
        """
        return await self.repository.delete(channel_id)

    async def toggle_active(
        self, channel_id: str, is_active: bool
    ) -> NotificationChannel | None:
        """Toggle channel active status.

        Args:
            channel_id: Channel ID.
            is_active: New active status.

        Returns:
            Updated channel or None if not found.
        """
        return await self.update(channel_id, is_active=is_active)

    def get_available_types(self) -> list[dict[str, Any]]:
        """Get available channel types with their schemas.

        Returns:
            Dictionary mapping type to schema.
        """
        return [
            {
                "type": channel_type,
                "name": channel_class.__name__.removesuffix("Channel"),
                "description": (channel_class.__doc__ or "").strip().splitlines()[0]
                if channel_class.__doc__
                else f"{channel_type.title()} notification channel",
                "config_schema": channel_class.get_config_schema(),
                "secret_fields": sorted(get_channel_secret_fields(channel_type)),
            }
            for channel_type, channel_class in sorted(ChannelRegistry._channels.items())
        ]


class NotificationRuleService:
    """Service for managing notification rules.

    Provides business logic for rule CRUD operations
    and condition matching.
    """

    # Valid condition types
    VALID_CONDITIONS = [
        "validation_failed",
        "critical_issues",
        "high_issues",
        "schedule_failed",
        "drift_detected",
        "schema_changed",
        "breaking_schema_change",
    ]

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.repository = NotificationRuleRepository(session)
        self.channel_repo = NotificationChannelRepository(session)

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        active_only: bool = False,
        condition: str | None = None,
    ) -> Sequence[NotificationRule]:
        """List notification rules.

        Args:
            offset: Number to skip.
            limit: Maximum to return.
            active_only: Only return active rules.
            condition: Optional condition filter.

        Returns:
            Sequence of rules.
        """
        if condition:
            rules = await self.repository.get_by_condition(
                condition, active_only=active_only
            )
            return rules[offset : offset + limit]

        if active_only:
            return await self.repository.get_active(offset=offset, limit=limit)

        return await self.repository.list(offset=offset, limit=limit)

    async def get_by_id(self, rule_id: str) -> NotificationRule | None:
        """Get rule by ID.

        Args:
            rule_id: Rule ID.

        Returns:
            Rule or None.
        """
        return await self.repository.get_by_id(rule_id)

    async def create(
        self,
        *,
        name: str,
        condition: str,
        channel_ids: list[str],
        condition_config: dict[str, Any] | None = None,
        source_ids: list[str] | None = None,
        is_active: bool = True,
    ) -> NotificationRule:
        """Create a new notification rule.

        Args:
            name: Rule name.
            condition: Trigger condition type.
            channel_ids: List of channel IDs to notify.
            condition_config: Optional condition configuration.
            source_ids: Optional source IDs to filter (None = all sources).
            is_active: Whether rule is active.

        Returns:
            Created rule.

        Raises:
            ValueError: If condition is invalid or channels don't exist.
        """
        # Validate condition
        if condition not in self.VALID_CONDITIONS:
            raise ValueError(
                f"Invalid condition: {condition}. "
                f"Valid conditions: {', '.join(self.VALID_CONDITIONS)}"
            )

        # Validate channel IDs exist
        if channel_ids:
            for channel_id in channel_ids:
                channel = await self.channel_repo.get_by_id(channel_id)
                if channel is None:
                    raise ValueError(f"Channel not found: {channel_id}")

        return await self.repository.create(
            name=name,
            condition=condition,
            channel_ids=channel_ids,
            condition_config=condition_config or {},
            source_ids=source_ids,
            is_active=is_active,
        )

    async def update(
        self,
        rule_id: str,
        *,
        name: str | None = None,
        condition: str | None = None,
        channel_ids: list[str] | None = None,
        condition_config: dict[str, Any] | None = None,
        source_ids: list[str] | None = None,
        is_active: bool | None = None,
    ) -> NotificationRule | None:
        """Update a notification rule.

        Args:
            rule_id: Rule ID.
            name: New name.
            condition: New condition.
            channel_ids: New channel IDs.
            condition_config: New condition config.
            source_ids: New source IDs.
            is_active: New active status.

        Returns:
            Updated rule or None if not found.

        Raises:
            ValueError: If condition or channel IDs are invalid.
        """
        rule = await self.repository.get_by_id(rule_id)
        if rule is None:
            return None

        # Validate condition if provided
        if condition is not None and condition not in self.VALID_CONDITIONS:
            raise ValueError(
                f"Invalid condition: {condition}. "
                f"Valid conditions: {', '.join(self.VALID_CONDITIONS)}"
            )

        # Validate channel IDs if provided
        if channel_ids is not None:
            for channel_id in channel_ids:
                channel = await self.channel_repo.get_by_id(channel_id)
                if channel is None:
                    raise ValueError(f"Channel not found: {channel_id}")

        # Build update data
        update_data: dict[str, Any] = {}
        if name is not None:
            update_data["name"] = name
        if condition is not None:
            update_data["condition"] = condition
        if channel_ids is not None:
            update_data["channel_ids"] = channel_ids
        if condition_config is not None:
            update_data["condition_config"] = condition_config
        if source_ids is not None:
            update_data["source_ids"] = source_ids
        if is_active is not None:
            update_data["is_active"] = is_active

        if not update_data:
            return rule

        return await self.repository.update(rule_id, **update_data)

    async def delete(self, rule_id: str) -> bool:
        """Delete a notification rule.

        Args:
            rule_id: Rule ID.

        Returns:
            True if deleted.
        """
        return await self.repository.delete(rule_id)

    async def toggle_active(
        self, rule_id: str, is_active: bool
    ) -> NotificationRule | None:
        """Toggle rule active status.

        Args:
            rule_id: Rule ID.
            is_active: New active status.

        Returns:
            Updated rule or None if not found.
        """
        return await self.update(rule_id, is_active=is_active)

    def get_valid_conditions(self) -> list[str]:
        """Get list of valid condition types.

        Returns:
            List of condition type strings.
        """
        return list(self.VALID_CONDITIONS)


class NotificationLogService:
    """Service for querying notification logs.

    Provides read-only access to notification delivery history.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.repository = NotificationLogRepository(session)

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        channel_id: str | None = None,
        status: str | None = None,
        hours: int | None = None,
    ) -> Sequence[NotificationLog]:
        """List notification logs.

        Args:
            offset: Number to skip.
            limit: Maximum to return.
            channel_id: Optional channel filter.
            status: Optional status filter.
            hours: Optional time range in hours.

        Returns:
            Sequence of logs.
        """
        if channel_id:
            return await self.repository.get_for_channel(channel_id, limit=limit)

        if hours:
            return await self.repository.get_recent(
                hours=hours, limit=limit, status=status
            )

        filters = []
        if status:
            filters.append(NotificationLog.status == status)

        return await self.repository.list(
            offset=offset,
            limit=limit,
            filters=filters if filters else None,
            order_by=NotificationLog.created_at.desc(),
        )

    async def get_by_id(self, log_id: str) -> NotificationLog | None:
        """Get log by ID.

        Args:
            log_id: Log ID.

        Returns:
            Log or None.
        """
        return await self.repository.get_by_id(log_id)

    async def get_stats(self, *, hours: int = 24) -> dict[str, Any]:
        """Get notification statistics.

        Args:
            hours: Time range in hours.

        Returns:
            Statistics dictionary.
        """
        return await self.repository.get_stats(hours=hours)
