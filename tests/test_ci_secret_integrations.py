from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from truthound_dashboard.core.connections import test_connection as run_connection_test
from truthound_dashboard.core.notifications.base import (
    ChannelRegistry,
    NotificationResult,
)
from truthound_dashboard.core.notifications.dispatcher import (
    TestNotificationEvent as NotificationTestEvent,
)
from truthound_dashboard.core.notifications.dispatcher import (
    create_dispatcher,
)
from truthound_dashboard.core.notifications.service import NotificationChannelService
from truthound_dashboard.db.database import init_db


@pytest.mark.asyncio
async def test_notification_secret_ref_dispatcher_smoke(tmp_path: Path) -> None:
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'notifications.sqlite3'}",
        connect_args={"check_same_thread": False},
    )

    try:
        await init_db(engine)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as session:
            service = NotificationChannelService(session)
            channel = await service.create(
                name="CI Slack",
                channel_type="slack",
                config={
                    "webhook_url": "https://hooks.slack.invalid/services/T000/B000/secret",
                    "channel": "#quality",
                },
                is_active=True,
            )
            await session.commit()

            stored = await service.get_by_id(channel.id)
            assert stored is not None
            assert "_secret_ref" in json.dumps(stored.config)

            materialized = await service.secrets.materialize_config(stored.config or {})
            assert materialized["webhook_url"].startswith("https://hooks.slack.invalid")

            dispatcher = create_dispatcher(session)
            captured_configs: list[dict[str, str]] = []

            class DummyChannel:
                def __init__(self, config: dict[str, str]) -> None:
                    self.config = config

                def format_message(self, event: object) -> str:
                    return "CI secret smoke notification"

                async def send_with_result(self, message: str, event: object) -> NotificationResult:
                    return NotificationResult(
                        success=True,
                        channel_id=stored.id,
                        channel_type=stored.type,
                        message=message,
                        error=None,
                    )

            original_create = ChannelRegistry.create

            def _create_channel(**kwargs: object) -> DummyChannel:
                config = kwargs["config"]
                assert isinstance(config, dict)
                captured_configs.append(config)
                return DummyChannel(config)

            ChannelRegistry.create = _create_channel
            try:
                result = await dispatcher._send_to_channel(
                    stored,
                    NotificationTestEvent(
                        source_id=stored.id,
                        source_name=stored.name,
                        channel_name=stored.name,
                    ),
                )
            finally:
                ChannelRegistry.create = original_create

            assert result.success is True
            assert captured_configs
            assert captured_configs[0]["webhook_url"].startswith("https://hooks.slack.invalid")
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_optional_source_connection_secret_smoke() -> None:
    if os.getenv("CI_SECRET_INTEGRATION_TARGET") == "notifications":
        pytest.skip("Source smoke disabled for notification-only runs")

    source_type = os.getenv("CI_SECRET_SMOKE_SOURCE_TYPE")
    source_config_json = os.getenv("CI_SECRET_SMOKE_SOURCE_CONFIG_JSON")
    if not source_type or not source_config_json:
        pytest.skip("Source smoke credentials are not configured")

    result = await run_connection_test(source_type, json.loads(source_config_json))
    assert result.get("success") is True, result
