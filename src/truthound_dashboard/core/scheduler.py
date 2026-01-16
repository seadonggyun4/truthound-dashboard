"""Validation scheduler with notification integration and maintenance.

This module provides scheduled validation execution with automatic
notification dispatch on failures, plus scheduled database maintenance.

The scheduler:
1. Runs scheduled validations based on flexible trigger types
2. Supports cron, interval, data change, composite, and event triggers
3. Triggers notifications on validation failures
4. Updates schedule run timestamps
5. Runs periodic database maintenance (cleanup, vacuum)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from truthound_dashboard.db import Schedule, Source, TriggerType, get_session

from .maintenance import get_maintenance_manager
from .notifications.dispatcher import create_dispatcher
from .services import ValidationService
from .truthound_adapter import get_adapter
from .triggers import TriggerFactory, TriggerContext, TriggerEvaluation

logger = logging.getLogger(__name__)


class ValidationScheduler:
    """Scheduler for automated validation runs with notifications.

    Manages scheduled validation jobs using APScheduler and integrates
    with the notification system to alert on failures.

    Supports multiple trigger types:
    - Cron: Traditional cron expressions
    - Interval: Fixed time intervals
    - DataChange: Profile-based change detection
    - Composite: Combined triggers with AND/OR logic
    - Event: Response to system events
    - Manual: API-only execution

    Also manages scheduled database maintenance tasks.

    Usage:
        scheduler = ValidationScheduler()
        await scheduler.start()
        # ... on shutdown ...
        await scheduler.stop()
    """

    # Default maintenance schedule: daily at 3:00 AM
    DEFAULT_MAINTENANCE_CRON = "0 3 * * *"
    # Alternative: run maintenance every 24 hours
    MAINTENANCE_INTERVAL_HOURS = 24
    # Data change trigger check interval
    DATA_CHANGE_CHECK_INTERVAL_SECONDS = 300  # 5 minutes

    def __init__(
        self,
        *,
        maintenance_enabled: bool = True,
        maintenance_cron: str | None = None,
        data_change_check_interval: int | None = None,
    ) -> None:
        """Initialize the scheduler.

        Args:
            maintenance_enabled: Whether to enable scheduled maintenance.
            maintenance_cron: Cron expression for maintenance schedule.
                Defaults to daily at 3:00 AM.
            data_change_check_interval: Interval in seconds for checking
                data change triggers. Defaults to 5 minutes.
        """
        self._scheduler = AsyncIOScheduler()
        self._jobs: dict[str, str] = {}  # schedule_id -> job_id mapping
        self._maintenance_enabled = maintenance_enabled
        self._maintenance_cron = maintenance_cron or self.DEFAULT_MAINTENANCE_CRON
        self._maintenance_job_id = "system_maintenance"
        self._data_change_job_id = "data_change_check"
        self._data_change_check_interval = (
            data_change_check_interval or self.DATA_CHANGE_CHECK_INTERVAL_SECONDS
        )

    async def start(self) -> None:
        """Start the scheduler and load existing schedules."""
        logger.info("Starting validation scheduler")
        self._scheduler.start()
        await self._load_schedules()

        # Start maintenance schedule if enabled
        if self._maintenance_enabled:
            self._schedule_maintenance()

        # Start data change trigger checker
        self._schedule_data_change_checker()

    async def stop(self) -> None:
        """Stop the scheduler."""
        logger.info("Stopping validation scheduler")
        self._scheduler.shutdown(wait=False)

    def _schedule_maintenance(self) -> None:
        """Schedule periodic database maintenance."""
        try:
            trigger = CronTrigger.from_crontab(self._maintenance_cron)
            self._scheduler.add_job(
                self._run_maintenance,
                trigger=trigger,
                id=self._maintenance_job_id,
                name="Database Maintenance",
                replace_existing=True,
            )
            logger.info(
                f"Scheduled database maintenance: {self._maintenance_cron}"
            )
        except Exception as e:
            logger.error(f"Failed to schedule maintenance: {e}")

    def enable_maintenance(self, cron: str | None = None) -> None:
        """Enable scheduled maintenance.

        Args:
            cron: Optional cron expression override.
        """
        self._maintenance_enabled = True
        if cron:
            self._maintenance_cron = cron
        self._schedule_maintenance()

    def disable_maintenance(self) -> None:
        """Disable scheduled maintenance."""
        self._maintenance_enabled = False
        try:
            self._scheduler.remove_job(self._maintenance_job_id)
            logger.info("Disabled scheduled maintenance")
        except Exception:
            pass  # Job may not exist

    def get_maintenance_next_run(self) -> datetime | None:
        """Get next scheduled maintenance run time.

        Returns:
            Next run datetime or None if disabled.
        """
        if not self._maintenance_enabled:
            return None
        try:
            job = self._scheduler.get_job(self._maintenance_job_id)
            if job:
                return job.next_run_time
        except Exception:
            pass
        return None

    async def _run_maintenance(self) -> None:
        """Execute scheduled database maintenance."""
        logger.info("Running scheduled database maintenance")

        manager = get_maintenance_manager()

        if not manager.config.enabled:
            logger.info("Maintenance is disabled in configuration")
            return

        try:
            report = await manager.run_cleanup()

            logger.info(
                f"Maintenance completed: {report.total_deleted} records deleted "
                f"in {report.total_duration_ms}ms "
                f"(vacuum: {report.vacuum_performed})"
            )

            if not report.success:
                failed_tasks = [r.task_name for r in report.results if not r.success]
                logger.warning(f"Some maintenance tasks failed: {failed_tasks}")

        except Exception as e:
            logger.error(f"Maintenance failed: {e}")

    async def _load_schedules(self) -> None:
        """Load active schedules from database."""
        async with get_session() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(Schedule).where(Schedule.is_active == True)
            )
            schedules = result.scalars().all()

            for schedule in schedules:
                self.add_schedule(schedule)

    def add_schedule(self, schedule: Schedule) -> None:
        """Add a schedule to the scheduler.

        Supports multiple trigger types:
        - Cron/Interval: Traditional APScheduler triggers
        - DataChange/Composite/Event: Evaluated by periodic checker

        Args:
            schedule: Schedule model to add.
        """
        if schedule.id in self._jobs:
            self.remove_schedule(schedule.id)

        trigger_type = schedule.effective_trigger_type

        # Manual and event triggers don't need APScheduler jobs
        if trigger_type in (TriggerType.MANUAL, TriggerType.EVENT):
            logger.info(
                f"Schedule {schedule.name} uses {trigger_type.value} trigger - "
                "no APScheduler job needed"
            )
            return

        # Data change and composite triggers are handled by periodic checker
        if trigger_type in (TriggerType.DATA_CHANGE, TriggerType.COMPOSITE):
            logger.info(
                f"Schedule {schedule.name} uses {trigger_type.value} trigger - "
                "will be checked periodically"
            )
            return

        try:
            # Create APScheduler trigger based on type
            if trigger_type == TriggerType.CRON:
                cron_expr = schedule.effective_cron_expression
                if not cron_expr:
                    logger.error(f"Cron schedule {schedule.id} missing expression")
                    return
                ap_trigger = CronTrigger.from_crontab(cron_expr)
                trigger_desc = cron_expr

            elif trigger_type == TriggerType.INTERVAL:
                config = schedule.trigger_config or {}
                seconds = config.get("seconds", 0)
                minutes = config.get("minutes", 0)
                hours = config.get("hours", 0)
                days = config.get("days", 0)

                total_seconds = seconds + minutes * 60 + hours * 3600 + days * 86400
                if total_seconds <= 0:
                    total_seconds = 3600  # Default to 1 hour

                ap_trigger = IntervalTrigger(seconds=total_seconds)
                trigger_desc = f"every {total_seconds}s"

            else:
                # Fallback for unknown types - try as cron
                cron_expr = schedule.cron_expression or "0 0 * * *"
                ap_trigger = CronTrigger.from_crontab(cron_expr)
                trigger_desc = cron_expr

            job = self._scheduler.add_job(
                self._run_validation,
                trigger=ap_trigger,
                args=[schedule.id],
                id=f"schedule_{schedule.id}",
                name=f"Validation: {schedule.name}",
                replace_existing=True,
            )
            self._jobs[schedule.id] = job.id
            logger.info(f"Added schedule: {schedule.name} ({trigger_desc})")

        except Exception as e:
            logger.error(f"Failed to add schedule {schedule.id}: {e}")

    def remove_schedule(self, schedule_id: str) -> None:
        """Remove a schedule from the scheduler.

        Args:
            schedule_id: Schedule ID to remove.
        """
        job_id = self._jobs.pop(schedule_id, None)
        if job_id:
            try:
                self._scheduler.remove_job(job_id)
                logger.info(f"Removed schedule: {schedule_id}")
            except Exception as e:
                logger.error(f"Failed to remove schedule {schedule_id}: {e}")

    def update_schedule(self, schedule: Schedule) -> None:
        """Update a schedule in the scheduler.

        Args:
            schedule: Updated schedule model.
        """
        if schedule.is_active:
            self.add_schedule(schedule)
        else:
            self.remove_schedule(schedule.id)

    async def _run_validation(self, schedule_id: str) -> None:
        """Execute a scheduled validation.

        Args:
            schedule_id: ID of the schedule to run.
        """
        logger.info(f"Running scheduled validation: {schedule_id}")

        async with get_session() as session:
            from sqlalchemy import select

            # Get schedule
            result = await session.execute(
                select(Schedule).where(Schedule.id == schedule_id)
            )
            schedule = result.scalar_one_or_none()

            if schedule is None:
                logger.error(f"Schedule not found: {schedule_id}")
                return

            if not schedule.is_active:
                logger.info(f"Schedule is inactive: {schedule_id}")
                return

            # Get source
            result = await session.execute(
                select(Source).where(Source.id == schedule.source_id)
            )
            source = result.scalar_one_or_none()

            if source is None:
                logger.error(f"Source not found for schedule: {schedule_id}")
                return

            # Run validation
            validation_service = ValidationService(session)
            config = schedule.config or {}

            try:
                validation = await validation_service.run_validation(
                    schedule.source_id,
                    validators=config.get("validators"),
                    schema_path=config.get("schema_path"),
                    auto_schema=config.get("auto_schema", False),
                )

                # Update schedule run time
                schedule.mark_run(self._get_next_run(schedule.cron_expression))
                await session.commit()

                logger.info(
                    f"Validation completed for schedule {schedule_id}: "
                    f"passed={validation.passed}"
                )

                # Send notifications if failed and notifications are enabled
                if schedule.notify_on_failure and not validation.passed:
                    await self._send_failure_notification(
                        session=session,
                        source=source,
                        schedule=schedule,
                        validation=validation,
                    )

            except Exception as e:
                logger.error(f"Validation failed for schedule {schedule_id}: {e}")

                # Send error notification
                if schedule.notify_on_failure:
                    await self._send_error_notification(
                        session=session,
                        source=source,
                        schedule=schedule,
                        error_message=str(e),
                    )

    async def _send_failure_notification(
        self,
        session: Any,
        source: Source,
        schedule: Schedule,
        validation: Any,
    ) -> None:
        """Send notification for validation failure.

        Args:
            session: Database session.
            source: Source that was validated.
            schedule: Schedule that triggered the validation.
            validation: Validation result.
        """
        dispatcher = create_dispatcher(session)

        try:
            results = await dispatcher.notify_schedule_failed(
                source_id=source.id,
                source_name=source.name,
                schedule_id=schedule.id,
                schedule_name=schedule.name,
                validation_id=validation.id,
                error_message=f"Validation failed with {validation.total_issues or 0} issues",
            )
            await session.commit()

            success_count = sum(1 for r in results if r.success)
            logger.info(
                f"Sent {success_count}/{len(results)} failure notifications "
                f"for schedule {schedule.id}"
            )
        except Exception as e:
            logger.error(f"Failed to send notifications: {e}")

    async def _send_error_notification(
        self,
        session: Any,
        source: Source,
        schedule: Schedule,
        error_message: str,
    ) -> None:
        """Send notification for validation error.

        Args:
            session: Database session.
            source: Source that was validated.
            schedule: Schedule that triggered the validation.
            error_message: Error message.
        """
        dispatcher = create_dispatcher(session)

        try:
            results = await dispatcher.notify_schedule_failed(
                source_id=source.id,
                source_name=source.name,
                schedule_id=schedule.id,
                schedule_name=schedule.name,
                error_message=error_message,
            )
            await session.commit()

            success_count = sum(1 for r in results if r.success)
            logger.info(
                f"Sent {success_count}/{len(results)} error notifications "
                f"for schedule {schedule.id}"
            )
        except Exception as e:
            logger.error(f"Failed to send error notifications: {e}")

    def _get_next_run(self, cron_expression: str) -> datetime | None:
        """Calculate next run time from cron expression.

        Args:
            cron_expression: Cron expression.

        Returns:
            Next run datetime or None if invalid.
        """
        try:
            trigger = CronTrigger.from_crontab(cron_expression)
            return trigger.get_next_fire_time(None, datetime.utcnow())
        except Exception:
            return None

    def _schedule_data_change_checker(self) -> None:
        """Schedule periodic checker for data change and composite triggers."""
        try:
            self._scheduler.add_job(
                self._check_data_change_triggers,
                trigger=IntervalTrigger(seconds=self._data_change_check_interval),
                id=self._data_change_job_id,
                name="Data Change Trigger Checker",
                replace_existing=True,
            )
            logger.info(
                f"Scheduled data change checker: every {self._data_change_check_interval}s"
            )
        except Exception as e:
            logger.error(f"Failed to schedule data change checker: {e}")

    async def _check_data_change_triggers(self) -> None:
        """Check all data change and composite triggers.

        This runs periodically to evaluate triggers that can't be
        handled by APScheduler's built-in triggers.
        """
        logger.debug("Checking data change triggers")

        async with get_session() as session:
            from sqlalchemy import select

            # Get schedules with data change or composite triggers
            result = await session.execute(
                select(Schedule)
                .where(Schedule.is_active == True)
                .where(
                    Schedule.trigger_type.in_([
                        TriggerType.DATA_CHANGE.value,
                        TriggerType.COMPOSITE.value,
                    ])
                )
            )
            schedules = result.scalars().all()

            if not schedules:
                logger.debug("No data change/composite schedules to check")
                return

            logger.info(f"Checking {len(schedules)} data change/composite schedules")

            for schedule in schedules:
                await self._evaluate_and_run_if_needed(session, schedule)

    async def _evaluate_and_run_if_needed(
        self, session: Any, schedule: Schedule
    ) -> None:
        """Evaluate a schedule's trigger and run validation if needed.

        Args:
            session: Database session.
            schedule: Schedule to evaluate.
        """
        try:
            # Get profile data for data change triggers
            profile_data = None
            baseline_profile = None

            if schedule.trigger_type == TriggerType.DATA_CHANGE.value:
                profile_data, baseline_profile = await self._get_profile_data(
                    session, schedule.source_id
                )

            # Evaluate trigger
            evaluation = await TriggerFactory.evaluate_schedule(
                schedule,
                profile_data=profile_data,
                baseline_profile=baseline_profile,
            )

            # Update schedule with evaluation result
            schedule.update_trigger_result(evaluation.to_dict())

            if evaluation.should_trigger:
                logger.info(
                    f"Trigger fired for schedule {schedule.name}: {evaluation.reason}"
                )
                # Run validation in background
                asyncio.create_task(self._run_validation(schedule.id))
            else:
                logger.debug(
                    f"Trigger not fired for schedule {schedule.name}: {evaluation.reason}"
                )

            await session.commit()

        except Exception as e:
            logger.error(f"Error evaluating schedule {schedule.id}: {e}")

    async def _get_profile_data(
        self, session: Any, source_id: str
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """Get current and baseline profile data for a source.

        Args:
            session: Database session.
            source_id: Source ID.

        Returns:
            Tuple of (current_profile, baseline_profile).
        """
        from sqlalchemy import select
        from truthound_dashboard.db import Profile

        try:
            # Get the two most recent profiles
            result = await session.execute(
                select(Profile)
                .where(Profile.source_id == source_id)
                .order_by(Profile.created_at.desc())
                .limit(2)
            )
            profiles = result.scalars().all()

            if len(profiles) == 0:
                return None, None
            elif len(profiles) == 1:
                return profiles[0].profile_json, None
            else:
                return profiles[0].profile_json, profiles[1].profile_json

        except Exception as e:
            logger.error(f"Error getting profile data for source {source_id}: {e}")
            return None, None

    async def trigger_event(
        self,
        event_type: str,
        source_id: str | None = None,
        event_data: dict[str, Any] | None = None,
    ) -> list[str]:
        """Trigger event-based schedules.

        Called when system events occur (e.g., schema change, drift detected).

        Args:
            event_type: Type of event (e.g., "schema_changed", "drift_detected").
            source_id: Optional source ID related to the event.
            event_data: Additional event data.

        Returns:
            List of schedule IDs that were triggered.
        """
        triggered_schedules = []

        async with get_session() as session:
            from sqlalchemy import select

            # Get event trigger schedules
            result = await session.execute(
                select(Schedule)
                .where(Schedule.is_active == True)
                .where(Schedule.trigger_type == TriggerType.EVENT.value)
            )
            schedules = result.scalars().all()

            full_event_data = {
                "type": event_type,
                "source_id": source_id,
                **(event_data or {}),
            }

            for schedule in schedules:
                evaluation = await TriggerFactory.evaluate_schedule(
                    schedule,
                    event_data=full_event_data,
                )

                if evaluation.should_trigger:
                    logger.info(
                        f"Event '{event_type}' triggered schedule {schedule.name}"
                    )
                    asyncio.create_task(self._run_validation(schedule.id))
                    triggered_schedules.append(schedule.id)

        return triggered_schedules


# Singleton instance
_scheduler: ValidationScheduler | None = None


def get_scheduler() -> ValidationScheduler:
    """Get the singleton scheduler instance.

    Returns:
        ValidationScheduler instance.
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = ValidationScheduler()
    return _scheduler


async def start_scheduler() -> None:
    """Start the validation scheduler."""
    scheduler = get_scheduler()
    await scheduler.start()


async def stop_scheduler() -> None:
    """Stop the validation scheduler."""
    scheduler = get_scheduler()
    await scheduler.stop()
