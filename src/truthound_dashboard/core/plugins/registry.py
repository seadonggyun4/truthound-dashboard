"""Registry-only plugin management."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db.models import Plugin, PluginStatus, PluginType

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Central registry for plugin inventory and lifecycle state."""

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}
        self._initialized = False

    async def initialize(self, session: AsyncSession) -> None:
        if self._initialized:
            return

        logger.info("Initializing plugin registry...")
        result = await session.execute(select(Plugin).where(Plugin.is_enabled == True))  # noqa: E712
        for plugin in result.scalars().all():
            self._plugins[plugin.name] = plugin
        self._initialized = True
        logger.info("Plugin registry initialized with %s active plugins", len(self._plugins))

    def clear_cache(self) -> None:
        self._plugins.clear()
        self._initialized = False

    async def list_plugins(
        self,
        session: AsyncSession,
        plugin_type: PluginType | None = None,
        status: PluginStatus | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[Plugin], int]:
        stmt = select(Plugin)
        count_stmt = select(func.count(Plugin.id))

        if plugin_type:
            stmt = stmt.where(Plugin.type == plugin_type.value)
            count_stmt = count_stmt.where(Plugin.type == plugin_type.value)
        if status:
            stmt = stmt.where(Plugin.status == status.value)
            count_stmt = count_stmt.where(Plugin.status == status.value)
        if search:
            search_pattern = f"%{search}%"
            predicate = (
                Plugin.name.ilike(search_pattern)
                | Plugin.display_name.ilike(search_pattern)
                | Plugin.description.ilike(search_pattern)
            )
            stmt = stmt.where(predicate)
            count_stmt = count_stmt.where(predicate)

        total = int((await session.scalar(count_stmt)) or 0)
        stmt = stmt.order_by(Plugin.created_at.desc()).offset(offset).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all(), total

    async def get_plugin(
        self,
        session: AsyncSession,
        plugin_id: str | None = None,
        name: str | None = None,
    ) -> Plugin | None:
        if plugin_id:
            stmt = select(Plugin).where(Plugin.id == plugin_id)
        elif name:
            stmt = select(Plugin).where(Plugin.name == name)
        else:
            return None

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def register_plugin(
        self,
        session: AsyncSession,
        name: str,
        display_name: str,
        description: str,
        version: str,
        plugin_type: PluginType,
        **kwargs: Any,
    ) -> Plugin:
        existing = await self.get_plugin(session, name=name)
        if existing:
            raise ValueError(f"Plugin with name '{name}' already exists")

        plugin = Plugin(
            name=name,
            display_name=display_name,
            description=description,
            version=version,
            type=plugin_type.value,
            **kwargs,
        )
        session.add(plugin)
        await session.flush()
        return plugin

    async def install_plugin(
        self,
        session: AsyncSession,
        plugin_id: str,
        enable: bool = True,
    ) -> Plugin:
        plugin = await self.get_plugin(session, plugin_id=plugin_id)
        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not found")

        plugin.install()
        if enable:
            plugin.enable()
            self._plugins[plugin.name] = plugin

        await session.flush()
        return plugin

    async def uninstall_plugin(
        self,
        session: AsyncSession,
        plugin_id: str,
        remove_data: bool = False,
    ) -> None:
        plugin = await self.get_plugin(session, plugin_id=plugin_id)
        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not found")

        self._plugins.pop(plugin.name, None)
        if remove_data:
            await session.delete(plugin)
        else:
            plugin.uninstall()
        await session.flush()

    async def enable_plugin(
        self,
        session: AsyncSession,
        plugin_id: str,
    ) -> Plugin:
        plugin = await self.get_plugin(session, plugin_id=plugin_id)
        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not found")

        plugin.enable()
        self._plugins[plugin.name] = plugin
        await session.flush()
        return plugin

    async def disable_plugin(
        self,
        session: AsyncSession,
        plugin_id: str,
    ) -> Plugin:
        plugin = await self.get_plugin(session, plugin_id=plugin_id)
        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not found")

        plugin.disable()
        self._plugins.pop(plugin.name, None)
        await session.flush()
        return plugin

    async def get_statistics(self, session: AsyncSession) -> dict[str, Any]:
        plugins = (await session.execute(select(Plugin))).scalars().all()

        by_type = {
            plugin_type.value: sum(1 for plugin in plugins if plugin.type == plugin_type.value)
            for plugin_type in PluginType
        }

        total_validators = sum(plugin.validators_count for plugin in plugins)
        total_reporters = sum(plugin.reporters_count for plugin in plugins)

        return {
            "total_plugins": len(plugins),
            "installed_plugins": sum(
                1 for plugin in plugins if plugin.status in (PluginStatus.INSTALLED.value, PluginStatus.ENABLED.value)
            ),
            "enabled_plugins": sum(1 for plugin in plugins if plugin.is_enabled),
            "plugins_by_type": by_type,
            "total_validators": total_validators,
            "enabled_validators": total_validators,
            "total_reporters": total_reporters,
            "enabled_reporters": total_reporters,
            "validator_categories": [],
            "cached_validators": 0,
            "cached_reporters": 0,
        }


plugin_registry = PluginRegistry()
