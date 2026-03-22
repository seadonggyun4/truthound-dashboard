from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from truthound_dashboard.core.notifications.base import NotificationEvent, NotificationResult
from truthound_dashboard.core.notifications.dispatcher import NotificationDispatcher
from truthound_dashboard.core.notifications.service import NotificationChannelService
from truthound_dashboard.db import NotificationChannel, SecretRef
from truthound_dashboard.db.database import init_db
from truthound_dashboard.time import utc_now


@pytest.mark.asyncio
async def test_notification_channel_migration_backfills_secret_refs(tmp_path: Path) -> None:
    db_path = tmp_path / "notification-secrets.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    try:
        async with engine.begin() as conn:
            now = utc_now()
            await conn.execute(
                text(
                    """
                    CREATE TABLE notification_channels (
                        id TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        name TEXT NOT NULL,
                        config TEXT NOT NULL,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    )
                    """
                )
            )
            await conn.execute(
                text(
                    """
                    INSERT INTO notification_channels (
                        id,
                        type,
                        name,
                        config,
                        is_active,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        :id,
                        :type,
                        :name,
                        :config,
                        :is_active,
                        :created_at,
                        :updated_at
                    )
                    """
                ),
                {
                    "id": "channel-legacy",
                    "type": "slack",
                    "name": "Legacy Slack",
                    "config": json.dumps(
                        {
                            "webhook_url": "https://hooks.slack.com/services/T000/B000/legacy-secret",
                            "channel": "#ops",
                        }
                    ),
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                },
            )

        await init_db(engine)

        async with engine.begin() as conn:
            channel_rows = await conn.execute(
                text(
                    """
                    SELECT config, config_version, credential_updated_at
                    FROM notification_channels
                    WHERE id = 'channel-legacy'
                    """
                )
            )
            config, config_version, credential_updated_at = channel_rows.one()
            config_dict = json.loads(config)

            secret_count_rows = await conn.execute(text("SELECT COUNT(*) FROM secret_refs"))
            secret_count = secret_count_rows.scalar_one()

        assert secret_count == 1
        assert isinstance(config_dict["webhook_url"], dict)
        assert "_secret_ref" in config_dict["webhook_url"]
        assert credential_updated_at is not None
        assert config_version == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_notification_channel_service_persists_and_rotates_secret_refs(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "notification-service.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    try:
        await init_db(engine)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as session:
            service = NotificationChannelService(session)
            channel = await service.create(
                name="Slack Alerts",
                channel_type="slack",
                config={
                    "webhook_url": "https://hooks.slack.com/services/T000/B000/created-secret",
                    "channel": "#alerts",
                },
            )
            await session.commit()

            assert isinstance(channel.config["webhook_url"], dict)
            assert "_secret_ref" in channel.config["webhook_url"]
            assert channel.credential_updated_at is not None

            result = await session.execute(select(SecretRef))
            secret_refs = result.scalars().all()
            assert len(secret_refs) == 1
            original_ref_id = secret_refs[0].id
            original_encrypted_value = secret_refs[0].encrypted_value
            original_credential_updated_at = channel.credential_updated_at

            updated_channel = await service.update(
                channel.id,
                config={"channel": "#platform-alerts"},
            )
            await session.commit()

            assert updated_channel is not None
            assert updated_channel.config["webhook_url"]["_secret_ref"] == original_ref_id
            assert updated_channel.credential_updated_at == original_credential_updated_at
            config_version_before_rotate = updated_channel.config_version

            rotated_channel = await service.rotate_credentials(
                channel.id,
                config={
                    "webhook_url": "https://hooks.slack.com/services/T000/B000/rotated-secret",
                },
            )
            await session.commit()

            assert rotated_channel is not None
            assert rotated_channel.config["webhook_url"]["_secret_ref"] == original_ref_id
            assert rotated_channel.config_version == config_version_before_rotate + 1

            result = await session.execute(select(SecretRef))
            rotated_secret_refs = result.scalars().all()
            assert len(rotated_secret_refs) == 1
            assert rotated_secret_refs[0].id == original_ref_id
            assert rotated_secret_refs[0].encrypted_value != original_encrypted_value
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_dispatcher_materializes_notification_secret_refs_before_runtime_use(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "notification-dispatch.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    try:
        await init_db(engine)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as session:
            channel = await NotificationChannelService(session).create(
                name="Slack Alerts",
                channel_type="slack",
                config={
                    "webhook_url": "https://hooks.slack.com/services/T000/B000/runtime-secret",
                    "channel": "#alerts",
                },
            )
            await session.flush()

            captured: dict[str, object] = {}

            class FakeChannel:
                def __init__(self, config: dict[str, object]) -> None:
                    self._config = config

                def format_message(self, event: NotificationEvent) -> str:
                    return f"event:{event.event_type}"

                async def send_with_result(
                    self,
                    message: str,
                    event: NotificationEvent | None = None,
                ) -> NotificationResult:
                    captured["config"] = self._config
                    captured["message"] = message
                    return NotificationResult(
                        success=True,
                        channel_id=channel.id,
                        channel_type=channel.type,
                        message=message,
                    )

            monkeypatch.setattr(
                "truthound_dashboard.core.notifications.dispatcher.ChannelRegistry.create",
                lambda **kwargs: FakeChannel(kwargs["config"]),
            )

            dispatcher = NotificationDispatcher(session, use_truthound=False)
            result = await dispatcher._send_to_channel(
                channel,
                NotificationEvent(event_type="test"),
            )

            assert result.success is True
            assert captured["message"] == "event:test"
            assert captured["config"] == {
                "webhook_url": "https://hooks.slack.com/services/T000/B000/runtime-secret",
                "channel": "#alerts",
            }
    finally:
        await engine.dispose()
