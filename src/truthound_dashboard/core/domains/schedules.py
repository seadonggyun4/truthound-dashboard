"""Schedule domain services and repositories."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db import BaseRepository, Schedule
from .sources import SourceRepository


class ScheduleRepository(BaseRepository[Schedule]):
    model = Schedule

    async def get_active(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ):
        return await self.list(
            offset=offset,
            limit=limit,
            filters=[Schedule.is_active],
        )

    async def get_for_source(
        self,
        source_id: str,
        *,
        limit: int = 50,
    ):
        return await self.list(
            limit=limit,
            filters=[Schedule.source_id == source_id],
            order_by=Schedule.created_at.desc(),
        )


class ScheduleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.source_repo = SourceRepository(session)
        self.schedule_repo = ScheduleRepository(session)

    async def create_schedule(
        self,
        source_id: str,
        *,
        name: str,
        cron_expression: str,
        trigger_type: str = "cron",
        trigger_config: dict[str, Any] | None = None,
        notify_on_failure: bool = True,
        config: dict[str, Any] | None = None,
    ) -> Schedule:
        source = await self.source_repo.get_by_id(source_id)
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")
        next_run = self._get_next_run(cron_expression)
        return await self.schedule_repo.create(
            name=name,
            source_id=source_id,
            cron_expression=cron_expression,
            trigger_type=trigger_type,
            trigger_config=trigger_config,
            is_active=True,
            notify_on_failure=notify_on_failure,
            next_run_at=next_run,
            config=config,
        )

    async def get_schedule(self, schedule_id: str) -> Schedule | None:
        return await self.schedule_repo.get_by_id(schedule_id)

    async def list_schedules(
        self,
        *,
        source_id: str | None = None,
        active_only: bool = False,
        limit: int = 100,
    ):
        if source_id:
            return await self.schedule_repo.get_for_source(source_id, limit=limit)
        if active_only:
            return await self.schedule_repo.get_active(limit=limit)
        return await self.schedule_repo.list(limit=limit)

    async def update_schedule(
        self,
        schedule_id: str,
        *,
        name: str | None = None,
        cron_expression: str | None = None,
        notify_on_failure: bool | None = None,
        config: dict[str, Any] | None = None,
    ) -> Schedule | None:
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if schedule is None:
            return None
        if name is not None:
            schedule.name = name
        if cron_expression is not None:
            schedule.cron_expression = cron_expression
            schedule.next_run_at = self._get_next_run(cron_expression)
        if notify_on_failure is not None:
            schedule.notify_on_failure = notify_on_failure
        if config is not None:
            schedule.config = config
        await self.session.flush()
        await self.session.refresh(schedule)
        return schedule

    async def delete_schedule(self, schedule_id: str) -> bool:
        return await self.schedule_repo.delete(schedule_id)

    async def pause_schedule(self, schedule_id: str) -> Schedule | None:
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if schedule is None:
            return None
        schedule.pause()
        await self.session.flush()
        await self.session.refresh(schedule)
        return schedule

    async def resume_schedule(self, schedule_id: str) -> Schedule | None:
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if schedule is None:
            return None
        schedule.resume()
        schedule.next_run_at = self._get_next_run(schedule.cron_expression)
        await self.session.flush()
        await self.session.refresh(schedule)
        return schedule

    def _get_next_run(self, cron_expression: str) -> datetime:
        try:
            from apscheduler.triggers.cron import CronTrigger

            trigger = CronTrigger.from_crontab(cron_expression)
            next_fire = trigger.get_next_fire_time(None, datetime.now().astimezone())
            if next_fire is None:
                raise ValueError("Could not calculate next run time")
            return next_fire
        except Exception as exc:
            raise ValueError(f"Invalid cron expression: {exc}") from exc


__all__ = ["ScheduleRepository", "ScheduleService"]
