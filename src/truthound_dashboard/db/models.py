"""SQLAlchemy models for the active Truthound 3.0 dashboard surface."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


from .base import Base, TimestampMixin, UUIDMixin
from truthound_dashboard.time import utc_now

# =============================================================================
# Schema Evolution Enums
# =============================================================================


class SchemaChangeType(str, Enum):
    """Type of schema change detected."""
    COLUMN_ADDED = "column_added"
    COLUMN_REMOVED = "column_removed"
    TYPE_CHANGED = "type_changed"


class SchemaChangeSeverity(str, Enum):
    """Severity level of schema change."""

    BREAKING = "breaking"
    NON_BREAKING = "non_breaking"


# =============================================================================
# Schedule Trigger Enums
# =============================================================================


class TriggerType(str, Enum):
    """Type of schedule trigger."""

    CRON = "cron"
    INTERVAL = "interval"
    DATA_CHANGE = "data_change"
    COMPOSITE = "composite"
    EVENT = "event"
    MANUAL = "manual"
    WEBHOOK = "webhook"  # External webhook triggers


class Source(Base, UUIDMixin, TimestampMixin):
    """Data source model.

    Represents a data source that can be validated.
    Supports various types: file, postgresql, mysql, snowflake, bigquery.

    Attributes:
        id: Unique identifier (UUID).
        name: Human-readable name for the source.
        type: Source type (file, postgresql, etc.).
        config: JSON configuration specific to source type.
        is_active: Whether the source is active.
        last_validated_at: Timestamp of last validation.
    """

    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    workspace_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    environment: Mapped[str] = mapped_column(String(32), nullable=False, default="production")
    config_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    credential_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __init__(self, **kwargs: Any) -> None:
        if "is_active" not in kwargs:
            kwargs["is_active"] = True
        super().__init__(**kwargs)

    # Relationships
    schemas: Mapped[list[Schema]] = relationship(
        "Schema",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    rules: Mapped[list[Rule]] = relationship(
        "Rule",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(Rule.created_at)",
    )
    validations: Mapped[list[Validation]] = relationship(
        "Validation",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(Validation.created_at)",
    )
    profiles: Mapped[list[Profile]] = relationship(
        "Profile",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(Profile.created_at)",
    )
    schedules: Mapped[list[Schedule]] = relationship(
        "Schedule",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    artifact_records: Mapped[list["ArtifactRecord"]] = relationship(
        "ArtifactRecord",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(ArtifactRecord.created_at)",
    )
    ownership: Mapped["SourceOwnership | None"] = relationship(
        "SourceOwnership",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin",
        uselist=False,
    )
    # Anomaly detections for this source
    anomaly_detections: Mapped[list["AnomalyDetection"]] = relationship(
        "AnomalyDetection",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    # Drift comparisons where this source is the baseline
    baseline_comparisons: Mapped[list["DriftComparison"]] = relationship(
        "DriftComparison",
        foreign_keys="[DriftComparison.baseline_source_id]",
        back_populates="baseline_source",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    # Drift comparisons where this source is the current
    current_comparisons: Mapped[list["DriftComparison"]] = relationship(
        "DriftComparison",
        foreign_keys="[DriftComparison.current_source_id]",
        back_populates="current_source",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    # Data masks for this source
    data_masks: Mapped[list["DataMask"]] = relationship(
        "DataMask",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    # PII scans for this source
    pii_scans: Mapped[list["PIIScan"]] = relationship(
        "PIIScan",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def source_path(self) -> str | None:
        """Get the data path from config."""
        return self.config.get("path") or self.config.get("connection_string")

    @property
    def latest_schema(self) -> Schema | None:
        """Get the most recent schema."""
        if self.schemas:
            return max(self.schemas, key=lambda s: s.created_at)
        return None

    @property
    def latest_validation(self) -> Validation | None:
        """Get the most recent validation."""
        if self.validations:
            return self.validations[0]
        return None

    @property
    def active_rules(self) -> list[Rule]:
        """Get all active rules for this source."""
        return [r for r in self.rules if r.is_active]

    @property
    def active_rule(self) -> Rule | None:
        """Get the active rule for this source (most recent)."""
        active = self.active_rules
        return active[0] if active else None

    @property
    def owner_user_id(self) -> str | None:
        ownership = getattr(self, "ownership", None)
        return ownership.owner_user_id if ownership is not None else None

    @property
    def owner_name(self) -> str | None:
        ownership = getattr(self, "ownership", None)
        if ownership is None or ownership.owner_user is None:
            return None
        return ownership.owner_user.display_name

    @property
    def team_id(self) -> str | None:
        ownership = getattr(self, "ownership", None)
        return ownership.team_id if ownership is not None else None

    @property
    def team_name(self) -> str | None:
        ownership = getattr(self, "ownership", None)
        if ownership is None or ownership.team is None:
            return None
        return ownership.team.name

    @property
    def domain_id(self) -> str | None:
        ownership = getattr(self, "ownership", None)
        return ownership.domain_id if ownership is not None else None

    @property
    def domain_name(self) -> str | None:
        ownership = getattr(self, "ownership", None)
        if ownership is None or ownership.domain is None:
            return None
        return ownership.domain.name


class Rule(Base, UUIDMixin, TimestampMixin):
    """Custom validation rules model.

    Stores custom validation rules for data sources in YAML format.
    Rules are used by truthound validators during validation runs.

    Attributes:
        id: Unique identifier (UUID).
        source_id: Reference to parent Source.
        name: Human-readable rule name.
        description: Optional description of the rule.
        rules_yaml: YAML content defining validation rules.
        rules_json: Parsed rules as JSON for programmatic access.
        is_active: Whether this rule set is currently active.
        version: Optional version string for tracking changes.

    Example rules_yaml format:
        columns:
          user_id:
            not_null: true
            unique: true
          email:
            pattern: "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$"
          age:
            min: 0
            max: 150
    """

    __tablename__ = "rules"

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="Default Rules",
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rules_yaml: Mapped[str] = mapped_column(Text, nullable=False)
    rules_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    source: Mapped[Source] = relationship("Source", back_populates="rules")

    @property
    def column_rules(self) -> dict[str, Any]:
        """Get column-level rules from JSON."""
        if self.rules_json and "columns" in self.rules_json:
            return self.rules_json["columns"]
        return {}

    @property
    def table_rules(self) -> dict[str, Any]:
        """Get table-level rules from JSON."""
        if self.rules_json and "table" in self.rules_json:
            return self.rules_json["table"]
        return {}

    @property
    def column_count(self) -> int:
        """Get number of columns with rules defined."""
        rules = self.column_rules
        return len(rules) if rules else 0

    def deactivate(self) -> None:
        """Mark this rule as inactive."""
        self.is_active = False

    def activate(self) -> None:
        """Mark this rule as active."""
        self.is_active = True


class Schema(Base, UUIDMixin, TimestampMixin):
    """Learned schema model.

    Stores truthound Schema objects (from th.learn) which contain:
    - Column definitions with dtype, nullable, unique, constraints
    - Row count and statistics
    - Version information

    Attributes:
        id: Unique identifier (UUID).
        source_id: Reference to parent Source.
        schema_yaml: YAML representation for display/editing.
        schema_json: Full schema as JSON for programmatic access.
        row_count: Number of rows when schema was learned.
        version: Schema version string.
        is_active: Whether this is the active schema for the source.
    """

    __tablename__ = "schemas"

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    schema_yaml: Mapped[str] = mapped_column(Text, nullable=False)
    schema_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    source: Mapped[Source] = relationship("Source", back_populates="schemas")

    @property
    def columns(self) -> list[str]:
        """Get list of column names from schema."""
        if self.schema_json and "columns" in self.schema_json:
            return list(self.schema_json["columns"].keys())
        return []


class Validation(Base, UUIDMixin):
    """Validation result model.

    Stores results from th.check validation runs.

    Attributes:
        id: Unique identifier (UUID).
        source_id: Reference to parent Source.
        status: Current status (pending, running, success, failed, error).
        passed: Whether validation passed (no issues).
        has_critical: Whether critical issues were found.
        has_high: Whether high severity issues were found.
        total_issues: Total number of issues found.
        result_json: Full validation result as JSON.
        duration_ms: Validation duration in milliseconds.
    """

    __tablename__ = "validations"

    # Composite index for efficient history queries (source + time ordering)
    __table_args__ = (
        Index("idx_validations_source_created", "source_id", "created_at"),
    )

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    # Validation results summary
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_critical: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_high: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    total_issues: Mapped[int | None] = mapped_column(Integer, nullable=True)
    critical_issues: Mapped[int | None] = mapped_column(Integer, nullable=True)
    high_issues: Mapped[int | None] = mapped_column(Integer, nullable=True)
    medium_issues: Mapped[int | None] = mapped_column(Integer, nullable=True)
    low_issues: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Data statistics
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Full result and timing
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    source: Mapped[Source] = relationship("Source", back_populates="validations")
    artifact_records: Mapped[list["ArtifactRecord"]] = relationship(
        "ArtifactRecord",
        back_populates="validation",
        lazy="selectin",
        order_by="desc(ArtifactRecord.created_at)",
    )

    @property
    def issues(self) -> list[dict[str, Any]]:
        """Get list of issues from result JSON."""
        if self.result_json and "issues" in self.result_json:
            return self.result_json["issues"]
        return []

    @property
    def is_complete(self) -> bool:
        """Check if validation has completed (success, failed, or error)."""
        return self.status in ("success", "failed", "error")

    def mark_started(self) -> None:
        """Mark validation as started."""
        self.status = "running"
        self.started_at = utc_now()

    def mark_completed(
        self,
        passed: bool,
        result: dict[str, Any],
    ) -> None:
        """Mark validation as completed with results."""
        self.status = "success" if passed else "failed"
        self.passed = passed
        self.result_json = result
        self.completed_at = utc_now()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

    def mark_error(self, message: str) -> None:
        """Mark validation as errored."""
        self.status = "error"
        self.error_message = message
        self.completed_at = utc_now()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)


class Profile(Base, UUIDMixin, TimestampMixin):
    """Data profile model.

    Stores profiling results from th.profile() for historical tracking.

    Attributes:
        id: Unique identifier (UUID).
        source_id: Reference to parent Source.
        profile_json: Full profile result as JSON.
        row_count: Number of rows profiled.
        column_count: Number of columns.
        size_bytes: Data size in bytes.
    """

    __tablename__ = "profiles"

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    source: Mapped[Source] = relationship("Source", back_populates="profiles")

    @property
    def columns(self) -> list[dict[str, Any]]:
        """Get column profiles from JSON."""
        if self.profile_json and "columns" in self.profile_json:
            return self.profile_json["columns"]
        return []


class Schedule(Base, UUIDMixin, TimestampMixin):
    """Validation schedule model.

    Manages scheduled validation runs with flexible trigger types.
    Supports cron, interval, data change detection, and composite triggers.

    Attributes:
        id: Unique identifier (UUID).
        name: Human-readable schedule name.
        source_id: Reference to Source to validate.
        trigger_type: Type of trigger (cron, interval, data_change, composite).
        trigger_config: JSON configuration specific to trigger type.
        cron_expression: Legacy cron expression (for backward compatibility).
        is_active: Whether schedule is active.
        notify_on_failure: Send notification on validation failure.
        last_run_at: Timestamp of last execution.
        next_run_at: Timestamp of next scheduled run.
        trigger_count: Total number of times this schedule has triggered.
        last_trigger_result: Result of last trigger evaluation.
        config: Additional configuration (validators, schema_path, etc.).
    """

    __tablename__ = "schedules"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # New flexible trigger system
    trigger_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=TriggerType.CRON.value,
        index=True,
    )
    trigger_config: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Trigger-specific configuration (threshold, metrics, etc.)",
    )
    # Legacy field for backward compatibility
    cron_expression: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_on_failure: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Trigger state tracking
    trigger_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_trigger_result: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Result of last trigger evaluation",
    )
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    source: Mapped[Source] = relationship("Source", back_populates="schedules")

    def pause(self) -> None:
        """Pause this schedule."""
        self.is_active = False

    def resume(self) -> None:
        """Resume this schedule."""
        self.is_active = True

    def mark_run(self, next_run: datetime | None = None) -> None:
        """Mark schedule as run and update next run time."""
        self.last_run_at = utc_now()
        self.next_run_at = next_run
        self.trigger_count += 1

    def update_trigger_result(self, result: dict[str, Any]) -> None:
        """Update the last trigger evaluation result."""
        self.last_trigger_result = result

    @property
    def effective_trigger_type(self) -> TriggerType:
        """Get the effective trigger type.

        Falls back to CRON if trigger_type is not set (legacy schedules).
        """
        try:
            return TriggerType(self.trigger_type)
        except ValueError:
            return TriggerType.CRON

    @property
    def effective_cron_expression(self) -> str | None:
        """Get the effective cron expression.

        For CRON triggers, returns the expression from trigger_config or legacy field.
        """
        if self.trigger_type == TriggerType.CRON.value:
            if self.trigger_config and "expression" in self.trigger_config:
                return self.trigger_config["expression"]
            return self.cron_expression
        return None

    def get_trigger_summary(self) -> str:
        """Get a human-readable summary of the trigger configuration."""
        trigger_type = self.effective_trigger_type

        if trigger_type == TriggerType.CRON:
            expr = self.effective_cron_expression
            return f"Cron: {expr}" if expr else "Cron: (not configured)"

        elif trigger_type == TriggerType.INTERVAL:
            if self.trigger_config:
                parts = []
                if self.trigger_config.get("days"):
                    parts.append(f"{self.trigger_config['days']}d")
                if self.trigger_config.get("hours"):
                    parts.append(f"{self.trigger_config['hours']}h")
                if self.trigger_config.get("minutes"):
                    parts.append(f"{self.trigger_config['minutes']}m")
                if self.trigger_config.get("seconds"):
                    parts.append(f"{self.trigger_config['seconds']}s")
                return f"Every {' '.join(parts)}" if parts else "Interval: (not configured)"
            return "Interval: (not configured)"

        elif trigger_type == TriggerType.DATA_CHANGE:
            threshold = self.trigger_config.get("change_threshold", 0.05) if self.trigger_config else 0.05
            return f"Data change >= {threshold * 100:.0f}%"

        elif trigger_type == TriggerType.COMPOSITE:
            if self.trigger_config:
                operator = self.trigger_config.get("operator", "and").upper()
                count = len(self.trigger_config.get("triggers", []))
                return f"Composite: {count} triggers ({operator})"
            return "Composite: (not configured)"

        elif trigger_type == TriggerType.EVENT:
            if self.trigger_config:
                events = self.trigger_config.get("event_types", [])
                return f"Events: {', '.join(events[:2])}{'...' if len(events) > 2 else ''}"
            return "Event: (not configured)"

        elif trigger_type == TriggerType.MANUAL:
            return "Manual trigger only"

        return f"{trigger_type.value}: (unknown)"


class DriftComparison(Base, UUIDMixin, TimestampMixin):
    """Drift comparison result model.

    Stores results from ``truthound.drift.compare()`` drift detection.

    Attributes:
        id: Unique identifier (UUID).
        baseline_source_id: Reference to baseline Source.
        current_source_id: Reference to current Source.
        has_drift: Whether drift was detected.
        has_high_drift: Whether high-severity drift was detected.
        total_columns: Total columns compared.
        drifted_columns: Number of columns with drift.
        result_json: Full comparison result as JSON.
        config: Comparison configuration (method, threshold, etc.).
    """

    __tablename__ = "drift_comparisons"

    baseline_source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    current_source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    has_drift: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_high_drift: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    total_columns: Mapped[int | None] = mapped_column(Integer, nullable=True)
    drifted_columns: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    baseline_source: Mapped[Source] = relationship(
        "Source",
        foreign_keys=[baseline_source_id],
        back_populates="baseline_comparisons",
    )
    current_source: Mapped[Source] = relationship(
        "Source",
        foreign_keys=[current_source_id],
        back_populates="current_comparisons",
    )

    @property
    def drift_percentage(self) -> float:
        """Calculate percentage of columns with drift."""
        if self.total_columns and self.total_columns > 0:
            return (self.drifted_columns or 0) / self.total_columns * 100
        return 0.0

    @property
    def column_results(self) -> list[dict[str, Any]]:
        """Get per-column drift results."""
        if self.result_json and "columns" in self.result_json:
            return self.result_json["columns"]
        return []


class MaskingStrategy(str, Enum):
    """Masking strategy enum."""

    REDACT = "redact"
    HASH = "hash"
    FAKE = "fake"


class DataMask(Base, UUIDMixin):
    """Data masking operation model.

    Stores results from th.mask() data masking operations.
    Supports three strategies: redact (asterisks), hash (SHA256), fake (realistic data).

    Attributes:
        id: Unique identifier (UUID).
        source_id: Reference to parent Source.
        status: Current status (pending, running, success, failed, error).
        strategy: Masking strategy used (redact, hash, fake).
        output_path: Path to the masked output file.
        columns_masked: List of columns that were masked.
        row_count: Number of rows processed.
        column_count: Number of columns in the data.
        auto_detected: Whether PII columns were auto-detected.
        result_json: Full mask result as JSON.
        duration_ms: Operation duration in milliseconds.
    """

    __tablename__ = "data_masks"

    # Composite index for efficient history queries (source + time ordering)
    __table_args__ = (
        Index("idx_data_masks_source_created", "source_id", "created_at"),
    )

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    # Masking configuration
    strategy: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=MaskingStrategy.REDACT.value,
        index=True,
    )
    output_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    columns_masked: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    auto_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Data statistics
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Full result and timing
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    source: Mapped[Source] = relationship(
        "Source",
        back_populates="data_masks",
    )

    @property
    def is_complete(self) -> bool:
        """Check if masking operation has completed."""
        return self.status in ("success", "failed", "error")

    @property
    def masked_column_count(self) -> int:
        """Get number of columns that were masked."""
        return len(self.columns_masked) if self.columns_masked else 0

    def mark_started(self) -> None:
        """Mark operation as started."""
        self.status = "running"
        self.started_at = utc_now()

    def mark_completed(
        self,
        result: dict[str, Any],
    ) -> None:
        """Mark operation as completed with results."""
        self.status = "success"
        self.result_json = result
        self.completed_at = utc_now()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

    def mark_error(self, message: str) -> None:
        """Mark operation as errored."""
        self.status = "error"
        self.error_message = message
        self.completed_at = utc_now()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)


class PIIScan(Base, UUIDMixin):
    """PII scan result model.

    Stores results from th.scan() PII detection runs.

    Attributes:
        id: Unique identifier (UUID).
        source_id: Reference to parent Source.
        status: Current status (pending, running, success, failed, error).
        total_columns_scanned: Total columns that were scanned.
        columns_with_pii: Number of columns containing PII.
        total_findings: Total number of PII findings.
        has_violations: Whether any regulation violations were found.
        total_violations: Number of regulation violations.
        min_confidence: Confidence threshold used for this scan.
        regulations_checked: List of regulations checked.
        result_json: Full scan result as JSON.
        duration_ms: Scan duration in milliseconds.
    """

    __tablename__ = "pii_scans"

    # Composite index for efficient history queries (source + time ordering)
    __table_args__ = (
        Index("idx_pii_scans_source_created", "source_id", "created_at"),
    )

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    # Scan summary
    total_columns_scanned: Mapped[int | None] = mapped_column(Integer, nullable=True)
    columns_with_pii: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_findings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_violations: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    total_violations: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Data statistics
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Configuration used
    min_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    regulations_checked: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Full result and timing
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    source: Mapped[Source] = relationship(
        "Source",
        back_populates="pii_scans",
    )

    @property
    def findings(self) -> list[dict[str, Any]]:
        """Get list of PII findings from result JSON."""
        if self.result_json and "findings" in self.result_json:
            return self.result_json["findings"]
        return []

    @property
    def violations(self) -> list[dict[str, Any]]:
        """Get list of regulation violations from result JSON."""
        if self.result_json and "violations" in self.result_json:
            return self.result_json["violations"]
        return []

    @property
    def is_complete(self) -> bool:
        """Check if scan has completed (success, failed, or error)."""
        return self.status in ("success", "failed", "error")

    def mark_started(self) -> None:
        """Mark scan as started."""
        self.status = "running"
        self.started_at = utc_now()

    def mark_completed(
        self,
        has_violations: bool,
        result: dict[str, Any],
    ) -> None:
        """Mark scan as completed with results."""
        self.status = "success" if not has_violations else "failed"
        self.has_violations = has_violations
        self.result_json = result
        self.completed_at = utc_now()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

    def mark_error(self, message: str) -> None:
        """Mark scan as errored."""
        self.status = "error"
        self.error_message = message
        self.completed_at = utc_now()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)


class AppSettings(Base):
    """Application settings model.

    Stores key-value configuration that can be modified at runtime.

    Attributes:
        key: Setting key (primary key).
        value: JSON value for the setting.
        description: Human-readable description.
    """

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


# =============================================================================
# Phase 3: Notification Models
# =============================================================================


class NotificationChannel(Base, UUIDMixin, TimestampMixin):
    """Notification channel configuration model.

    Represents a configured notification channel (Slack, Email, Webhook, etc.).
    Uses a polymorphic pattern where channel-specific configuration is stored
    in the 'config' JSON field.

    Attributes:
        id: Unique identifier (UUID).
        type: Channel type (slack, email, webhook, etc.).
        name: Human-readable channel name.
        config: JSON configuration specific to channel type.
        is_active: Whether channel is active.

    Example configs:
        Slack: {"webhook_url": "https://hooks.slack.com/..."}
        Email: {"smtp_host": "...", "smtp_port": 587, "recipients": [...]}
        Webhook: {"url": "...", "headers": {...}, "method": "POST"}
    """

    __tablename__ = "notification_channels"

    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    config_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    credential_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    logs: Mapped[list[NotificationLog]] = relationship(
        "NotificationLog",
        back_populates="channel",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def activate(self) -> None:
        """Activate this channel."""
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate this channel."""
        self.is_active = False

    def get_config_summary(self) -> str:
        """Get a safe summary of channel configuration (hides sensitive data)."""
        if self.type == "slack":
            url = self.config.get("webhook_url", "")
            return f"Webhook: ...{url[-20:]}" if len(url) > 20 else f"Webhook: {url}"
        elif self.type == "email":
            recipients = self.config.get("recipients", [])
            preview = ", ".join(recipients[:2])
            suffix = "..." if len(recipients) > 2 else ""
            return f"Recipients: {preview}{suffix}"
        elif self.type == "webhook":
            url = self.config.get("url", "")
            return f"URL: {url[:50]}..." if len(url) > 50 else f"URL: {url}"
        return "Configured"


class NotificationRule(Base, UUIDMixin, TimestampMixin):
    """Notification trigger rules model.

    Defines when and how notifications should be triggered based on
    validation events and conditions.

    Attributes:
        id: Unique identifier (UUID).
        name: Human-readable rule name.
        condition: Trigger condition type.
        condition_config: Additional condition configuration.
        channel_ids: List of channel IDs to notify.
        source_ids: Optional list of source IDs to filter (null = all sources).
        is_active: Whether rule is active.

    Condition types:
        - validation_failed: Any validation failure
        - critical_issues: Validation has critical issues
        - high_issues: Validation has high severity issues
        - schedule_failed: Scheduled validation failed
        - drift_detected: Drift detected in comparison
    """

    __tablename__ = "notification_rules"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    condition: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    condition_config: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, default=dict
    )
    channel_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    source_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def activate(self) -> None:
        """Activate this rule."""
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate this rule."""
        self.is_active = False

    def matches_source(self, source_id: str) -> bool:
        """Check if this rule applies to a given source.

        Args:
            source_id: Source ID to check.

        Returns:
            True if rule applies to this source.
        """
        if self.source_ids is None:
            return True  # Applies to all sources
        return source_id in self.source_ids


class NotificationLog(Base, UUIDMixin):
    """Notification delivery log model.

    Records all notification delivery attempts for auditing and debugging.

    Attributes:
        id: Unique identifier (UUID).
        channel_id: Reference to NotificationChannel.
        rule_id: Optional reference to NotificationRule that triggered this.
        event_type: Type of event that triggered notification.
        event_data: JSON data about the triggering event.
        status: Delivery status (pending, sent, failed).
        error_message: Error message if delivery failed.
        sent_at: Timestamp when notification was sent.
    """

    __tablename__ = "notification_logs"

    # Composite index for efficient queries
    __table_args__ = (
        Index("idx_notification_logs_channel_created", "channel_id", "created_at"),
        Index("idx_notification_logs_status", "status"),
    )

    channel_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("notification_channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("notification_rules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    channel: Mapped[NotificationChannel] = relationship(
        "NotificationChannel", back_populates="logs"
    )
    rule: Mapped[NotificationRule | None] = relationship(
        "NotificationRule", backref="logs"
    )

    def mark_sent(self) -> None:
        """Mark notification as successfully sent."""
        self.status = "sent"
        self.sent_at = utc_now()

    def mark_failed(self, error: str) -> None:
        """Mark notification as failed with error message."""
        self.status = "failed"
        self.error_message = error
        self.sent_at = utc_now()


# =============================================================================
# Schema Evolution Models
# =============================================================================


class SchemaVersion(Base, UUIDMixin, TimestampMixin):
    """Schema version snapshot for evolution tracking.

    Stores a snapshot of schema structure at a point in time
    to enable schema change detection and history tracking.

    Attributes:
        id: Unique identifier (UUID).
        source_id: Reference to parent Source.
        schema_id: Reference to the Schema record.
        version_number: Sequential version number for this source.
        schema_hash: SHA256 hash of normalized schema structure.
        column_snapshot: JSON snapshot of column definitions.
    """

    __tablename__ = "schema_versions"

    __table_args__ = (
        Index("idx_schema_versions_source", "source_id", "version_number"),
        Index("idx_schema_versions_hash", "schema_hash"),
    )

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    schema_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("schemas.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    column_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Relationships
    source: Mapped[Source] = relationship("Source", lazy="selectin")
    schema: Mapped[Schema] = relationship("Schema", lazy="selectin")

    @property
    def column_names(self) -> list[str]:
        """Get list of column names from snapshot."""
        return list(self.column_snapshot.keys())

    @property
    def column_count(self) -> int:
        """Get number of columns in this version."""
        return len(self.column_snapshot)


class SchemaChange(Base, UUIDMixin):
    """Individual schema change record.

    Records a single change detected between two schema versions.

    Attributes:
        id: Unique identifier (UUID).
        source_id: Reference to parent Source.
        from_version_id: Reference to previous SchemaVersion (null for first version).
        to_version_id: Reference to new SchemaVersion.
        change_type: Type of change (column_added, column_removed, type_changed).
        column_name: Name of the affected column.
        old_value: Previous value (for type changes).
        new_value: New value (for type changes or additions).
        severity: Severity of the change (breaking/non_breaking).
        created_at: When the change was detected.
    """

    __tablename__ = "schema_changes"

    __table_args__ = (
        Index("idx_schema_changes_source", "source_id", "created_at"),
        Index("idx_schema_changes_type", "change_type"),
    )

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_version_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("schema_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    to_version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("schema_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    change_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="non_breaking",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    # Relationships
    source: Mapped[Source] = relationship("Source", lazy="selectin")
    from_version: Mapped[SchemaVersion | None] = relationship(
        "SchemaVersion",
        foreign_keys=[from_version_id],
        lazy="selectin",
    )
    to_version: Mapped[SchemaVersion] = relationship(
        "SchemaVersion",
        foreign_keys=[to_version_id],
        lazy="selectin",
    )

    @property
    def is_breaking(self) -> bool:
        """Check if this is a breaking change."""
        return self.severity == "breaking"

    @property
    def description(self) -> str:
        """Generate human-readable description of the change."""
        if self.change_type == "column_added":
            return f"Column '{self.column_name}' added with type {self.new_value}"
        elif self.change_type == "column_removed":
            return f"Column '{self.column_name}' removed (was {self.old_value})"
        elif self.change_type == "type_changed":
            return f"Column '{self.column_name}' type changed from {self.old_value} to {self.new_value}"
        return f"Unknown change on '{self.column_name}'"


# =============================================================================
# Phase 14: Advanced Notification Models
# =============================================================================


class DeduplicationStrategyEnum(str, Enum):
    """Deduplication window strategies."""

    SLIDING = "sliding"
    TUMBLING = "tumbling"
    SESSION = "session"
    ADAPTIVE = "adaptive"


class DeduplicationPolicyEnum(str, Enum):
    """Deduplication policies."""

    NONE = "none"
    BASIC = "basic"
    SEVERITY = "severity"
    ISSUE_BASED = "issue_based"
    STRICT = "strict"
    CUSTOM = "custom"


class EscalationStateEnum(str, Enum):
    """Escalation incident states."""

    PENDING = "pending"
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class TargetTypeEnum(str, Enum):
    """Escalation target types."""

    USER = "user"
    GROUP = "group"
    ONCALL = "oncall"
    CHANNEL = "channel"


class RoutingRuleModel(Base, UUIDMixin, TimestampMixin):
    """Advanced routing rule model.

    Stores rule-based routing configuration for directing
    notifications to appropriate channels based on conditions.

    Attributes:
        id: Unique identifier (UUID).
        name: Human-readable rule name.
        rule_config: JSON configuration defining the rule logic.
        actions: List of channel IDs to notify when rule matches.
        priority: Priority for rule evaluation (higher = evaluated first).
        is_active: Whether rule is active.
        stop_on_match: Stop processing after this rule matches.
        metadata: Additional metadata.
    """

    __tablename__ = "routing_rules"

    workspace_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    rule_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    actions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    stop_on_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    routing_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    @property
    def rule_type(self) -> str:
        """Get the rule type from config."""
        return self.rule_config.get("type", "unknown")


class DeduplicationConfig(Base, UUIDMixin, TimestampMixin):
    """Deduplication configuration model.

    Stores configuration for notification deduplication
    to prevent duplicate notifications within time windows.

    Attributes:
        id: Unique identifier (UUID).
        name: Configuration name.
        strategy: Window strategy (sliding, tumbling, session, adaptive).
        policy: Deduplication policy (basic, severity, issue_based, etc.).
        window_seconds: Duration of deduplication window.
        is_active: Whether config is active.
    """

    __tablename__ = "deduplication_configs"

    __table_args__ = (
        Index("idx_dedup_config_workspace", "workspace_id"),
        Index("idx_dedup_config_is_active", "is_active"),
        Index("idx_dedup_config_strategy", "strategy"),
        Index("idx_dedup_config_policy", "policy"),
        Index("idx_dedup_config_created_at", "created_at"),
    )

    workspace_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    strategy: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DeduplicationStrategyEnum.SLIDING.value,
    )
    policy: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DeduplicationPolicyEnum.BASIC.value,
    )
    window_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ThrottlingConfig(Base, UUIDMixin, TimestampMixin):
    """Throttling configuration model.

    Stores rate limiting configuration for notifications
    to prevent overwhelming notification channels.

    Attributes:
        id: Unique identifier (UUID).
        name: Configuration name.
        per_minute: Max notifications per minute.
        per_hour: Max notifications per hour.
        per_day: Max notifications per day.
        burst_allowance: Factor to allow temporary bursts.
        channel_id: Optional channel ID for per-channel throttling.
        is_active: Whether config is active.
    """

    __tablename__ = "throttling_configs"

    __table_args__ = (
        Index("idx_throttle_config_workspace", "workspace_id"),
        Index("idx_throttle_config_is_active", "is_active"),
        Index("idx_throttle_config_created_at", "created_at"),
    )

    workspace_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    per_minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    per_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    burst_allowance: Mapped[float] = mapped_column(Float, default=1.5, nullable=False)
    channel_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("notification_channels.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    channel: Mapped[NotificationChannel | None] = relationship(
        "NotificationChannel",
        lazy="selectin",
    )


class EscalationPolicyModel(Base, UUIDMixin, TimestampMixin):
    """Escalation policy model.

    Stores multi-level escalation policy configuration
    for handling unacknowledged alerts.

    Attributes:
        id: Unique identifier (UUID).
        name: Policy name.
        description: Policy description.
        levels: JSON array of escalation levels.
        auto_resolve_on_success: Whether to auto-resolve on validation success.
        max_escalations: Maximum number of escalation attempts.
        is_active: Whether policy is active.
    """

    __tablename__ = "escalation_policies"

    workspace_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    levels: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    auto_resolve_on_success: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    max_escalations: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    incidents: Mapped[list[EscalationIncidentModel]] = relationship(
        "EscalationIncidentModel",
        back_populates="policy",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def level_count(self) -> int:
        """Get number of escalation levels."""
        return len(self.levels) if self.levels else 0


class EscalationIncidentModel(Base, UUIDMixin):
    """Escalation incident model.

    Tracks the lifecycle of an escalation from trigger to resolution.

    Attributes:
        id: Unique identifier (UUID).
        policy_id: Reference to escalation policy.
        incident_ref: External reference (e.g., validation ID).
        state: Current incident state.
        current_level: Current escalation level.
        escalation_count: Number of escalation attempts.
        context: JSON context data.
        acknowledged_by: Who acknowledged the incident.
        acknowledged_at: When acknowledged.
        resolved_by: Who resolved the incident.
        resolved_at: When resolved.
        events: JSON array of state transition events.
        next_escalation_at: When next escalation will occur.
    """

    __tablename__ = "escalation_incidents"

    __table_args__ = (
        Index("idx_escalation_incidents_policy", "policy_id"),
        Index("idx_escalation_incidents_ref", "incident_ref"),
        Index("idx_escalation_incidents_state", "state"),
        Index("idx_escalation_incidents_workspace", "workspace_id"),
        Index("idx_escalation_incidents_queue", "queue_id"),
        Index("idx_escalation_incidents_assignee", "assignee_user_id"),
        Index("idx_escalation_incidents_created_at", "created_at"),
        Index("idx_escalation_incidents_state_created", "state", "created_at"),
    )

    policy_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("escalation_policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    queue_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("incident_queues.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assignee_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    incident_ref: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    state: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=EscalationStateEnum.PENDING.value,
        index=True,
    )
    current_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    escalation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    context: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    acknowledged_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    events: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    next_escalation_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationships
    policy: Mapped[EscalationPolicyModel] = relationship(
        "EscalationPolicyModel",
        back_populates="incidents",
    )
    queue: Mapped[Any | None] = relationship(
        "IncidentQueue",
        back_populates="incidents",
        foreign_keys=[queue_id],
        lazy="selectin",
    )
    assignee_user: Mapped[Any | None] = relationship(
        "User",
        foreign_keys=[assignee_user_id],
        lazy="selectin",
    )
    assigned_by_user: Mapped[Any | None] = relationship(
        "User",
        foreign_keys=[assigned_by],
        lazy="selectin",
    )

    @property
    def is_active(self) -> bool:
        """Check if incident is active (not resolved)."""
        return self.state != EscalationStateEnum.RESOLVED.value

    @property
    def is_acknowledged(self) -> bool:
        """Check if incident has been acknowledged."""
        return self.state == EscalationStateEnum.ACKNOWLEDGED.value

    @property
    def is_resolved(self) -> bool:
        """Check if incident is resolved."""
        return self.state == EscalationStateEnum.RESOLVED.value

    def can_escalate(self, max_escalations: int) -> bool:
        """Check if incident can be escalated further.

        Args:
            max_escalations: Maximum allowed escalations from policy.

        Returns:
            True if escalation is allowed, False otherwise.
        """
        # Cannot escalate resolved or acknowledged incidents
        if self.state in (
            EscalationStateEnum.RESOLVED.value,
            EscalationStateEnum.ACKNOWLEDGED.value,
        ):
            return False

        # Check escalation count limit
        if self.escalation_count >= max_escalations:
            return False

        return True

    def escalate(
        self,
        next_level: int,
        next_escalation_at: datetime | None,
        max_escalations: int,
    ) -> bool:
        """Attempt to escalate the incident.

        Thread-safe escalation with validation. Returns False if
        escalation is not allowed.

        Args:
            next_level: The new escalation level.
            next_escalation_at: When the next escalation should occur.
            max_escalations: Maximum allowed escalations.

        Returns:
            True if escalation succeeded, False if not allowed.
        """
        if not self.can_escalate(max_escalations):
            return False

        old_state = self.state
        self.state = EscalationStateEnum.ESCALATED.value
        self.current_level = next_level
        self.escalation_count += 1
        self.next_escalation_at = next_escalation_at
        self.updated_at = utc_now()

        self.add_event(
            from_state=old_state,
            to_state=EscalationStateEnum.ESCALATED.value,
            actor="system",
            message=f"Escalated to level {next_level}",
        )

        return True

    def add_event(
        self,
        from_state: str | None,
        to_state: str,
        actor: str | None = None,
        message: str = "",
    ) -> None:
        """Add a state transition event."""
        event = {
            "from_state": from_state,
            "to_state": to_state,
            "actor": actor,
            "message": message,
            "timestamp": utc_now().isoformat(),
        }
        if self.events is None:
            self.events = []
        self.events.append(event)


# =============================================================================
# Scheduler Job Model (Persistent Job Storage)
# =============================================================================


class SchedulerJobState(str, Enum):
    """State of a scheduled job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    MISFIRED = "misfired"
    PAUSED = "paused"


class SchedulerJob(Base, UUIDMixin):
    """Persistent scheduler job model.

    Stores scheduled jobs for APScheduler with SQLAlchemy backend,
    enabling job persistence across restarts.

    Features:
        - Survives process restarts
        - Supports exponential backoff retries
        - Tracks execution history
        - Enables job recovery on startup

    Attributes:
        id: Unique job identifier (UUID).
        name: Human-readable job name.
        func_ref: Reference to the function to execute (module:function).
        trigger_type: Type of trigger (interval, cron, date).
        trigger_args: Arguments for the trigger configuration.
        args: Positional arguments for the function.
        kwargs: Keyword arguments for the function.
        next_run_time: Next scheduled execution time.
        state: Current job state.
        retry_count: Number of retry attempts.
        last_run_time: Last execution time.
        last_error: Last error message.
        job_metadata: Additional job metadata.
        created_at: When the job was created.
        updated_at: Last update timestamp.
    """

    __tablename__ = "scheduler_jobs"

    __table_args__ = (
        Index("idx_scheduler_jobs_state", "state"),
        Index("idx_scheduler_jobs_next_run", "next_run_time"),
        Index("idx_scheduler_jobs_state_next_run", "state", "next_run_time"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    func_ref: Mapped[str] = mapped_column(String(512), nullable=False)
    trigger_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="interval",
    )
    trigger_args: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    args: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    kwargs: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    next_run_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )
    state: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SchedulerJobState.PENDING.value,
        index=True,
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_run_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    @property
    def is_due(self) -> bool:
        """Check if job is due for execution."""
        if not self.next_run_time:
            return False
        return (
            self.state in (SchedulerJobState.PENDING.value, SchedulerJobState.MISFIRED.value)
            and utc_now() >= self.next_run_time
        )

    @property
    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.state == SchedulerJobState.RUNNING.value

    @property
    def is_completed(self) -> bool:
        """Check if job has completed successfully."""
        return self.state == SchedulerJobState.COMPLETED.value

    @property
    def is_failed(self) -> bool:
        """Check if job has failed permanently."""
        return self.state == SchedulerJobState.FAILED.value

    def mark_running(self) -> None:
        """Mark job as running."""
        self.state = SchedulerJobState.RUNNING.value
        self.last_run_time = utc_now()
        self.updated_at = utc_now()

    def mark_completed(self, next_run_time: datetime | None = None) -> None:
        """Mark job as completed.

        Args:
            next_run_time: Next scheduled run time (for recurring jobs).
        """
        if next_run_time:
            self.state = SchedulerJobState.PENDING.value
            self.next_run_time = next_run_time
        else:
            self.state = SchedulerJobState.COMPLETED.value
        self.retry_count = 0
        self.last_error = None
        self.updated_at = utc_now()

    def mark_failed(self, error: str, can_retry: bool = True) -> None:
        """Mark job as failed.

        Args:
            error: Error message.
            can_retry: Whether job can be retried.
        """
        self.last_error = error
        self.updated_at = utc_now()

        if can_retry:
            self.state = SchedulerJobState.PENDING.value
            self.retry_count += 1
        else:
            self.state = SchedulerJobState.FAILED.value

    def mark_misfired(self) -> None:
        """Mark job as misfired."""
        self.state = SchedulerJobState.MISFIRED.value
        self.updated_at = utc_now()
        if self.job_metadata is None:
            self.job_metadata = {}
        self.job_metadata["misfire_count"] = self.job_metadata.get("misfire_count", 0) + 1
        self.job_metadata["last_misfire_at"] = utc_now().isoformat()


# =============================================================================
# Phase 10: Data Lineage Models
# =============================================================================


class LineageNodeType(str, Enum):
    """Type of lineage node."""

    SOURCE = "source"
    TRANSFORM = "transform"
    SINK = "sink"


class LineageEdgeType(str, Enum):
    """Type of lineage edge."""

    DERIVES_FROM = "derives_from"
    TRANSFORMS_TO = "transforms_to"
    JOINS_WITH = "joins_with"
    FILTERS_FROM = "filters_from"


class LineageNode(Base, UUIDMixin, TimestampMixin):
    """Data lineage node model.

    Represents a node in the data lineage graph (source, transformation, or sink).

    Attributes:
        id: Unique identifier (UUID).
        name: Human-readable node name.
        node_type: Type of node (source, transform, sink).
        source_id: Optional reference to a data source.
        metadata_json: Additional metadata for the node.
        position_x: X coordinate for graph visualization.
        position_y: Y coordinate for graph visualization.
    """

    __tablename__ = "lineage_nodes"

    __table_args__ = (
        Index("idx_lineage_nodes_type", "node_type"),
        Index("idx_lineage_nodes_source", "source_id"),
        Index("idx_lineage_nodes_name_type", "name", "node_type", unique=True),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    node_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=LineageNodeType.SOURCE.value,
        index=True,
    )
    source_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    position_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    position_y: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    source: Mapped[Source | None] = relationship(
        "Source",
        lazy="selectin",
    )
    outgoing_edges: Mapped[list[LineageEdge]] = relationship(
        "LineageEdge",
        foreign_keys="LineageEdge.source_node_id",
        back_populates="source_node",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    incoming_edges: Mapped[list[LineageEdge]] = relationship(
        "LineageEdge",
        foreign_keys="LineageEdge.target_node_id",
        back_populates="target_node",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def upstream_count(self) -> int:
        """Get number of upstream (incoming) connections."""
        return len(self.incoming_edges)

    @property
    def downstream_count(self) -> int:
        """Get number of downstream (outgoing) connections."""
        return len(self.outgoing_edges)

    @property
    def is_source_type(self) -> bool:
        """Check if this is a source node."""
        return self.node_type == LineageNodeType.SOURCE.value

    @property
    def is_transform_type(self) -> bool:
        """Check if this is a transform node."""
        return self.node_type == LineageNodeType.TRANSFORM.value

    @property
    def is_sink_type(self) -> bool:
        """Check if this is a sink node."""
        return self.node_type == LineageNodeType.SINK.value


class LineageEdge(Base, UUIDMixin):
    """Data lineage edge model.

    Represents a connection (data flow) between two lineage nodes.

    Attributes:
        id: Unique identifier (UUID).
        source_node_id: ID of the source node (origin of data flow).
        target_node_id: ID of the target node (destination of data flow).
        edge_type: Type of relationship.
        metadata_json: Additional metadata for the edge.
        created_at: When the edge was created.
    """

    __tablename__ = "lineage_edges"

    __table_args__ = (
        Index("idx_lineage_edges_source", "source_node_id"),
        Index("idx_lineage_edges_target", "target_node_id"),
        Index(
            "idx_lineage_edges_unique",
            "source_node_id",
            "target_node_id",
            "edge_type",
            unique=True,
        ),
    )

    source_node_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("lineage_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_node_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("lineage_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    edge_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=LineageEdgeType.DERIVES_FROM.value,
        index=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    # Relationships
    source_node: Mapped[LineageNode] = relationship(
        "LineageNode",
        foreign_keys=[source_node_id],
        back_populates="outgoing_edges",
    )
    target_node: Mapped[LineageNode] = relationship(
        "LineageNode",
        foreign_keys=[target_node_id],
        back_populates="incoming_edges",
    )


# =============================================================================
# OpenLineage Webhook Models
# =============================================================================


class OpenLineageEventType(str, Enum):
    """Types of OpenLineage events that can be emitted."""

    JOB = "job"
    DATASET = "dataset"
    ALL = "all"


class OpenLineageWebhook(Base, UUIDMixin, TimestampMixin):
    """OpenLineage webhook configuration model.

    Stores configuration for emitting OpenLineage events to external endpoints.

    Attributes:
        id: Unique identifier (UUID).
        name: Human-readable name for the webhook.
        url: Target URL for the webhook.
        is_active: Whether the webhook is enabled.
        headers_json: Custom headers as JSON (excluding auth).
        api_key: Optional API key for authentication.
        event_types: Types of events to emit (job, dataset, all).
        batch_size: Number of events per batch.
        timeout_seconds: Request timeout.
        last_sent_at: Timestamp of last successful emission.
        success_count: Total successful emissions.
        failure_count: Total failed emissions.
        last_error: Last error message if any.
    """

    __tablename__ = "openlineage_webhooks"

    __table_args__ = (
        Index("idx_openlineage_webhooks_active", "is_active"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    headers_json: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)
    api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_types: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=OpenLineageEventType.ALL.value,
    )
    batch_size: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    # Statistics
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    @property
    def headers(self) -> dict[str, str]:
        """Get headers dictionary."""
        return self.headers_json or {}

    @property
    def total_emissions(self) -> int:
        """Get total emission attempts."""
        return self.success_count + self.failure_count

    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_emissions == 0:
            return 100.0
        return (self.success_count / self.total_emissions) * 100

    def record_success(self) -> None:
        """Record a successful emission."""
        self.success_count += 1
        self.last_sent_at = utc_now()
        self.last_error = None

    def record_failure(self, error: str) -> None:
        """Record a failed emission."""
        self.failure_count += 1
        self.last_error = error

    def activate(self) -> None:
        """Enable the webhook."""
        self.is_active = True

    def deactivate(self) -> None:
        """Disable the webhook."""
        self.is_active = False


# =============================================================================
# Phase 10: Anomaly Detection Models
# =============================================================================


class AnomalyAlgorithm(str, Enum):
    """Supported anomaly detection algorithms."""

    ISOLATION_FOREST = "isolation_forest"
    LOF = "lof"
    ONE_CLASS_SVM = "one_class_svm"
    DBSCAN = "dbscan"
    STATISTICAL = "statistical"
    AUTOENCODER = "autoencoder"


class AnomalyDetectionStatus(str, Enum):
    """Status of an anomaly detection run."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


class AnomalyDetection(Base, UUIDMixin):
    """Anomaly detection result model.

    Stores results from ML-based anomaly detection runs.

    Attributes:
        id: Unique identifier (UUID).
        source_id: Reference to parent Source.
        status: Current status (pending, running, success, error).
        algorithm: Detection algorithm used.
        config: Algorithm-specific configuration.
        total_rows: Total rows analyzed.
        anomaly_count: Number of anomalies found.
        anomaly_rate: Rate of anomalies (0-1).
        columns_analyzed: List of columns that were analyzed.
        result_json: Full detection result as JSON.
        duration_ms: Execution time in milliseconds.
        error_message: Error message if failed.
    """

    __tablename__ = "anomaly_detections"

    __table_args__ = (
        Index("idx_anomaly_detections_source_created", "source_id", "created_at"),
        Index("idx_anomaly_detections_status", "status"),
        Index("idx_anomaly_detections_algorithm", "algorithm"),
    )

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AnomalyDetectionStatus.PENDING.value,
        index=True,
    )

    # Algorithm configuration
    algorithm: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=AnomalyAlgorithm.ISOLATION_FOREST.value,
        index=True,
    )
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Results summary
    total_rows: Mapped[int | None] = mapped_column(Integer, nullable=True)
    anomaly_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    anomaly_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    columns_analyzed: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Full result and timing
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    source: Mapped[Source] = relationship(
        "Source",
        back_populates="anomaly_detections",
    )

    @property
    def is_complete(self) -> bool:
        """Check if detection has completed (success or error)."""
        return self.status in (
            AnomalyDetectionStatus.SUCCESS.value,
            AnomalyDetectionStatus.ERROR.value,
        )

    @property
    def anomalies(self) -> list[dict[str, Any]]:
        """Get list of anomaly records from result JSON."""
        if self.result_json and "anomalies" in self.result_json:
            return self.result_json["anomalies"]
        return []

    @property
    def column_summaries(self) -> list[dict[str, Any]]:
        """Get per-column anomaly summaries from result JSON."""
        if self.result_json and "column_summaries" in self.result_json:
            return self.result_json["column_summaries"]
        return []

    def mark_started(self) -> None:
        """Mark detection as started."""
        self.status = AnomalyDetectionStatus.RUNNING.value
        self.started_at = utc_now()

    def mark_completed(
        self,
        anomaly_count: int,
        anomaly_rate: float,
        result: dict[str, Any],
    ) -> None:
        """Mark detection as completed with results."""
        self.status = AnomalyDetectionStatus.SUCCESS.value
        self.anomaly_count = anomaly_count
        self.anomaly_rate = anomaly_rate
        self.result_json = result
        self.completed_at = utc_now()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

    def mark_error(self, message: str) -> None:
        """Mark detection as errored."""
        self.status = AnomalyDetectionStatus.ERROR.value
        self.error_message = message
        self.completed_at = utc_now()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)


class AnomalyExplanation(Base, UUIDMixin):
    """SHAP/LIME explanations for anomaly detection results.

    Stores feature-level explanations for individual anomalous rows,
    providing interpretability for ML-based anomaly detection.

    Attributes:
        id: Unique identifier (UUID).
        detection_id: Reference to parent AnomalyDetection.
        row_index: Row index in the original dataset.
        anomaly_score: Anomaly score for this row.
        feature_contributions: JSON array of feature contributions.
        total_shap: Sum of all SHAP values.
        summary: Human-readable explanation summary.
        generated_at: When the explanation was generated.
    """

    __tablename__ = "anomaly_explanations"

    __table_args__ = (
        Index("idx_anomaly_explanations_detection", "detection_id"),
        Index("idx_anomaly_explanations_row", "detection_id", "row_index"),
    )

    detection_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("anomaly_detections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Row identification
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Anomaly information
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)

    # SHAP/LIME explanation data
    feature_contributions: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    total_shap: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Human-readable summary
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    # Timestamp
    generated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    # Relationships
    detection: Mapped[AnomalyDetection] = relationship(
        "AnomalyDetection",
        backref="explanations",
    )

    @property
    def top_features(self) -> list[str]:
        """Get names of top contributing features."""
        if not self.feature_contributions:
            return []
        return [fc.get("feature", "") for fc in self.feature_contributions[:5]]

    @property
    def contribution_count(self) -> int:
        """Get number of feature contributions stored."""
        return len(self.feature_contributions) if self.feature_contributions else 0


class BatchDetectionStatus(str, Enum):
    """Status of a batch anomaly detection job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"  # Some sources completed with errors
    ERROR = "error"
    CANCELLED = "cancelled"


class AnomalyBatchJob(Base, UUIDMixin, TimestampMixin):
    """Batch anomaly detection job model.

    Stores configuration and results for batch anomaly detection
    across multiple data sources.

    Attributes:
        id: Unique identifier (UUID).
        name: Optional job name.
        status: Current status of the batch job.
        algorithm: Detection algorithm to use.
        config: Algorithm-specific configuration.
        source_ids: List of source IDs to process.
        total_sources: Total number of sources.
        completed_sources: Number of completed sources.
        failed_sources: Number of failed sources.
        total_anomalies: Total anomalies found across all sources.
        results_json: Detection results per source.
        error_message: Error message if job failed.
        duration_ms: Total execution time in milliseconds.
    """

    __tablename__ = "anomaly_batch_jobs"

    __table_args__ = (
        Index("idx_anomaly_batch_jobs_status", "status"),
        Index("idx_anomaly_batch_jobs_created", "created_at"),
    )

    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=BatchDetectionStatus.PENDING.value,
        index=True,
    )

    # Algorithm configuration
    algorithm: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=AnomalyAlgorithm.ISOLATION_FOREST.value,
    )
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Sources to process
    source_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    # Progress tracking
    total_sources: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_sources: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_sources: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_source_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Aggregate results
    total_anomalies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_rows_analyzed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Per-source results: {source_id: {detection_id, status, anomaly_count, anomaly_rate, ...}}
    results_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timing
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    @property
    def progress_percent(self) -> float:
        """Get progress as percentage."""
        if self.total_sources == 0:
            return 0.0
        return ((self.completed_sources + self.failed_sources) / self.total_sources) * 100

    @property
    def average_anomaly_rate(self) -> float:
        """Get average anomaly rate across all successful sources."""
        if not self.results_json:
            return 0.0
        rates = [
            r["anomaly_rate"]
            for r in self.results_json.values()
            if r.get("status") == "success" and r.get("anomaly_rate") is not None
        ]
        return sum(rates) / len(rates) if rates else 0.0

    @property
    def is_complete(self) -> bool:
        """Check if batch job has completed."""
        return self.status in (
            BatchDetectionStatus.COMPLETED.value,
            BatchDetectionStatus.PARTIAL.value,
            BatchDetectionStatus.ERROR.value,
            BatchDetectionStatus.CANCELLED.value,
        )

    def mark_started(self) -> None:
        """Mark batch job as started."""
        self.status = BatchDetectionStatus.RUNNING.value
        self.started_at = utc_now()

    def update_progress(
        self,
        source_id: str,
        detection_id: str,
        status: str,
        anomaly_count: int = 0,
        anomaly_rate: float = 0.0,
        total_rows: int = 0,
        error_message: str | None = None,
    ) -> None:
        """Update progress for a single source."""
        if self.results_json is None:
            self.results_json = {}

        self.results_json[source_id] = {
            "detection_id": detection_id,
            "status": status,
            "anomaly_count": anomaly_count,
            "anomaly_rate": anomaly_rate,
            "total_rows": total_rows,
            "error_message": error_message,
        }

        if status == "success":
            self.completed_sources += 1
            self.total_anomalies += anomaly_count
            self.total_rows_analyzed += total_rows
        elif status == "error":
            self.failed_sources += 1

    def mark_completed(self) -> None:
        """Mark batch job as completed."""
        if self.failed_sources > 0 and self.completed_sources > 0:
            self.status = BatchDetectionStatus.PARTIAL.value
        elif self.failed_sources == self.total_sources:
            self.status = BatchDetectionStatus.ERROR.value
        else:
            self.status = BatchDetectionStatus.COMPLETED.value

        self.completed_at = utc_now()
        self.current_source_id = None

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

    def mark_error(self, message: str) -> None:
        """Mark batch job as errored."""
        self.status = BatchDetectionStatus.ERROR.value
        self.error_message = message
        self.completed_at = utc_now()
        self.current_source_id = None

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

    def mark_cancelled(self) -> None:
        """Mark batch job as cancelled."""
        self.status = BatchDetectionStatus.CANCELLED.value
        self.completed_at = utc_now()
        self.current_source_id = None

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

# =============================================================================
# Plugin Inventory Models
# =============================================================================


class PluginType(str, Enum):
    """Type of plugin."""

    VALIDATOR = "validator"
    REPORTER = "reporter"
    CONNECTOR = "connector"
    TRANSFORMER = "transformer"


class PluginStatus(str, Enum):
    """Installation status of a plugin."""

    AVAILABLE = "available"
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UPDATE_AVAILABLE = "update_available"
    ERROR = "error"


class PluginSource(str, Enum):
    """Source of the plugin."""

    OFFICIAL = "official"
    COMMUNITY = "community"
    LOCAL = "local"
    PRIVATE = "private"


class SecurityLevel(str, Enum):
    """Security level of the plugin."""

    TRUSTED = "trusted"
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    SANDBOXED = "sandboxed"


class Plugin(Base, UUIDMixin, TimestampMixin):
    """Plugin model.

    Represents an installable plugin in the plugin marketplace.

    Attributes:
        id: Unique identifier (UUID).
        name: Plugin name (unique identifier).
        display_name: Human-readable display name.
        description: Plugin description.
        version: Current/installed version.
        latest_version: Latest available version.
        type: Plugin type (validator, reporter, connector, transformer).
        source: Plugin source (official, community, local, private).
        status: Installation status.
        security_level: Security verification level.
        author: Author information (JSON).
        license: License identifier.
        homepage: Plugin homepage URL.
        repository: Repository URL.
        keywords: Search keywords (JSON array).
        categories: Plugin categories (JSON array).
        dependencies: Plugin dependencies (JSON array).
        permissions: Required permissions (JSON array).
        python_version: Required Python version.
        dashboard_version: Required dashboard version.
        icon_url: Plugin icon URL.
        banner_url: Plugin banner URL.
        documentation_url: Documentation URL.
        changelog: Changelog markdown.
        readme: README markdown.
        package_url: URL to download plugin package.
        signature: Plugin signature info (JSON).
        sandbox_config: Sandbox configuration (JSON).
        is_enabled: Whether plugin is enabled.
        install_count: Total installation count.
        rating: Average rating (1-5).
        rating_count: Number of ratings.
        validators_count: Number of validators provided.
        reporters_count: Number of reporters provided.
        installed_at: When plugin was installed.
        last_updated: When plugin was last updated.
    """

    __tablename__ = "plugins"

    __table_args__ = (
        Index("idx_plugins_name", "name", unique=True),
        Index("idx_plugins_type", "type"),
        Index("idx_plugins_source", "source"),
        Index("idx_plugins_status", "status"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    latest_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    type: Mapped[str] = mapped_column(
        SQLEnum(PluginType, native_enum=False, length=20),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(
        SQLEnum(PluginSource, native_enum=False, length=20),
        nullable=False,
        default=PluginSource.COMMUNITY.value,
    )
    status: Mapped[str] = mapped_column(
        SQLEnum(PluginStatus, native_enum=False, length=20),
        nullable=False,
        default=PluginStatus.AVAILABLE.value,
        index=True,
    )
    security_level: Mapped[str] = mapped_column(
        SQLEnum(SecurityLevel, native_enum=False, length=20),
        nullable=False,
        default=SecurityLevel.UNVERIFIED.value,
    )
    author: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    license: Mapped[str | None] = mapped_column(String(50), nullable=True)
    homepage: Mapped[str | None] = mapped_column(String(500), nullable=True)
    repository: Mapped[str | None] = mapped_column(String(500), nullable=True)
    keywords: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    categories: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    dependencies: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    permissions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    python_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dashboard_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    banner_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    documentation_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    readme: Mapped[str | None] = mapped_column(Text, nullable=True)
    package_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    signature: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    sandbox_config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    install_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    validators_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reporters_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    installed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def install(self) -> None:
        """Mark plugin as installed."""
        self.status = PluginStatus.INSTALLED.value
        self.installed_at = utc_now()
        self.install_count += 1

    def enable(self) -> None:
        """Enable the plugin."""
        self.status = PluginStatus.ENABLED.value
        self.is_enabled = True

    def disable(self) -> None:
        """Disable the plugin."""
        self.status = PluginStatus.DISABLED.value
        self.is_enabled = False

    def uninstall(self) -> None:
        """Mark plugin as available (uninstalled)."""
        self.status = PluginStatus.AVAILABLE.value
        self.is_enabled = False
        self.installed_at = None

    def update_rating(self, new_rating: float) -> None:
        """Update average rating with a new rating."""
        if self.rating is None:
            self.rating = new_rating
        else:
            total = self.rating * self.rating_count + new_rating
            self.rating = total / (self.rating_count + 1)
        self.rating_count += 1


# =============================================================================
# Storage Tiering Models (truthound 1.2.10+)
# =============================================================================


class TierType(str, Enum):
    """Storage tier types."""

    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    ARCHIVE = "archive"


class MigrationDirection(str, Enum):
    """Migration direction for tier policies."""

    DEMOTE = "demote"
    PROMOTE = "promote"


class TierPolicyType(str, Enum):
    """Types of tier policies."""

    AGE_BASED = "age_based"
    ACCESS_BASED = "access_based"
    SIZE_BASED = "size_based"
    SCHEDULED = "scheduled"
    COMPOSITE = "composite"
    CUSTOM = "custom"


class StorageTierModel(Base, UUIDMixin, TimestampMixin):
    """Storage tier definition model.

    Represents a storage tier with its backend configuration.

    Attributes:
        id: Unique identifier (UUID).
        name: Unique tier name (hot, warm, cold, archive, or custom).
        tier_type: Type classification (HOT, WARM, COLD, ARCHIVE).
        store_type: Backend store type (filesystem, s3, gcs, etc.).
        store_config: JSON configuration for the store backend.
        priority: Read order priority (lower = higher priority).
        cost_per_gb: Cost per GB for cost analysis.
        retrieval_time_ms: Expected retrieval latency in milliseconds.
        tier_metadata: Additional tier metadata.
        is_active: Whether the tier is active.
    """

    __tablename__ = "storage_tiers"

    __table_args__ = (
        Index("idx_storage_tiers_name", "name", unique=True),
        Index("idx_storage_tiers_type", "tier_type"),
        Index("idx_storage_tiers_priority", "priority"),
    )

    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    tier_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TierType.HOT.value,
    )
    store_type: Mapped[str] = mapped_column(String(50), nullable=False)
    store_config: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    cost_per_gb: Mapped[float | None] = mapped_column(Float, nullable=True)
    retrieval_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tier_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    policies_from: Mapped[list["TierPolicyModel"]] = relationship(
        "TierPolicyModel",
        foreign_keys="TierPolicyModel.from_tier_id",
        back_populates="from_tier",
        lazy="selectin",
    )
    policies_to: Mapped[list["TierPolicyModel"]] = relationship(
        "TierPolicyModel",
        foreign_keys="TierPolicyModel.to_tier_id",
        back_populates="to_tier",
        lazy="selectin",
    )


class TierPolicyModel(Base, UUIDMixin, TimestampMixin):
    """Tier migration policy model.

    Stores tier migration policy configuration including composite policies.
    Supports AgeBasedTierPolicy, AccessBasedTierPolicy, SizeBasedTierPolicy,
    ScheduledTierPolicy, CompositeTierPolicy, and CustomTierPolicy.

    Attributes:
        id: Unique identifier (UUID).
        name: Policy name.
        description: Policy description.
        policy_type: Type of policy (age_based, access_based, etc.).
        from_tier_id: Source tier ID.
        to_tier_id: Destination tier ID.
        direction: Migration direction (demote/promote).
        config: JSON configuration specific to policy type.
        is_active: Whether policy is active.
        priority: Execution priority (lower = runs first).
        parent_id: Parent composite policy ID (for nested policies).
    """

    __tablename__ = "tier_policies"

    __table_args__ = (
        Index("idx_tier_policies_name", "name"),
        Index("idx_tier_policies_type", "policy_type"),
        Index("idx_tier_policies_from_tier", "from_tier_id"),
        Index("idx_tier_policies_to_tier", "to_tier_id"),
        Index("idx_tier_policies_parent", "parent_id"),
        Index("idx_tier_policies_active", "is_active"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    policy_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=TierPolicyType.AGE_BASED.value,
    )
    from_tier_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("storage_tiers.id", ondelete="CASCADE"),
        nullable=False,
    )
    to_tier_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("storage_tiers.id", ondelete="CASCADE"),
        nullable=False,
    )
    direction: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=MigrationDirection.DEMOTE.value,
    )
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tier_policies.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Relationships
    from_tier: Mapped["StorageTierModel"] = relationship(
        "StorageTierModel",
        foreign_keys=[from_tier_id],
        back_populates="policies_from",
        lazy="selectin",
    )
    to_tier: Mapped["StorageTierModel"] = relationship(
        "StorageTierModel",
        foreign_keys=[to_tier_id],
        back_populates="policies_to",
        lazy="selectin",
    )
    parent: Mapped["TierPolicyModel | None"] = relationship(
        "TierPolicyModel",
        remote_side="TierPolicyModel.id",
        back_populates="children",
        foreign_keys=[parent_id],
    )
    children: Mapped[list["TierPolicyModel"]] = relationship(
        "TierPolicyModel",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def is_composite(self) -> bool:
        """Check if this is a composite policy."""
        return self.policy_type == TierPolicyType.COMPOSITE.value

    @property
    def child_count(self) -> int:
        """Get number of child policies."""
        return len(self.children) if self.children else 0


class TieringConfigModel(Base, UUIDMixin, TimestampMixin):
    """Tiering configuration model.

    Stores the main tiering configuration including default tier,
    promotion settings, and batch processing options.

    Attributes:
        id: Unique identifier (UUID).
        name: Configuration name.
        default_tier_id: Default tier for new items.
        enable_promotion: Whether to auto-promote on frequent access.
        promotion_threshold: Access count to trigger promotion.
        check_interval_hours: Hours between auto-checks.
        batch_size: Items per migration batch.
        enable_parallel_migration: Whether to enable parallel migration.
        max_parallel_migrations: Maximum concurrent migrations.
        is_active: Whether configuration is active.
    """

    __tablename__ = "tiering_configs"

    __table_args__ = (
        Index("idx_tiering_configs_name", "name", unique=True),
        Index("idx_tiering_configs_active", "is_active"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_tier_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("storage_tiers.id", ondelete="SET NULL"),
        nullable=True,
    )
    enable_promotion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    promotion_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    check_interval_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    batch_size: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    enable_parallel_migration: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    max_parallel_migrations: Mapped[int] = mapped_column(
        Integer, nullable=False, default=4
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    default_tier: Mapped["StorageTierModel | None"] = relationship(
        "StorageTierModel",
        foreign_keys=[default_tier_id],
        lazy="selectin",
    )


class TierMigrationHistoryModel(Base, UUIDMixin):
    """Tier migration history model.

    Tracks migration operations for auditing and analysis.

    Attributes:
        id: Unique identifier (UUID).
        policy_id: Reference to the policy that triggered migration.
        item_id: ID of the migrated item.
        from_tier_id: Source tier ID.
        to_tier_id: Destination tier ID.
        size_bytes: Size of migrated item.
        started_at: When migration started.
        completed_at: When migration completed.
        status: Migration status (pending, in_progress, completed, failed).
        error_message: Error message if failed.
    """

    __tablename__ = "tier_migration_history"

    __table_args__ = (
        Index("idx_tier_migration_policy", "policy_id"),
        Index("idx_tier_migration_item", "item_id"),
        Index("idx_tier_migration_status", "status"),
        Index("idx_tier_migration_started", "started_at"),
    )

    policy_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tier_policies.id", ondelete="SET NULL"),
        nullable=True,
    )
    item_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    from_tier_id: Mapped[str] = mapped_column(String(36), nullable=False)
    to_tier_id: Mapped[str] = mapped_column(String(36), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    @property
    def duration_ms(self) -> float | None:
        """Calculate migration duration in milliseconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None
