"""Source-related Pydantic schemas.

This module defines schemas for data source API operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field, field_validator

from truthound_dashboard.core.encryption import redact_config

from .base import BaseSchema, IDMixin, ListResponseWrapper, TimestampMixin

# Supported source types - must match SourceType enum in connections.py
SourceType = Literal[
    # File-based
    "file",
    "csv",
    "parquet",
    "json",
    "ndjson",
    "jsonl",
    # Core SQL
    "postgresql",
    "mysql",
    "sqlite",
    # Cloud Data Warehouses
    "snowflake",
    "bigquery",
    "redshift",
    "databricks",
    # Enterprise
    "oracle",
    "sqlserver",
    # Big Data
    "spark",
    # NoSQL
    "mongodb",
    "elasticsearch",
    # Streaming
    "kafka",
]

# Source type categories for UI grouping
SourceCategory = Literal["file", "database", "warehouse", "bigdata", "nosql", "streaming"]

# Field types for dynamic form rendering
FieldType = Literal["text", "password", "number", "select", "boolean", "file_path", "textarea"]


class SourceBase(BaseSchema):
    """Base source schema with common fields."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable source name",
        examples=["Sales Data", "User Events"],
    )
    type: SourceType = Field(
        ...,
        description="Data source type",
        examples=["file", "postgresql"],
    )
    config: dict[str, Any] = Field(
        ...,
        description="Source-specific configuration",
        examples=[{"path": "/data/sales.csv"}],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional source description",
    )
    environment: str = Field(
        default="production",
        description="Deployment environment for the source",
        examples=["production", "staging"],
    )
    workspace_id: str | None = Field(
        default=None,
        description="Owning workspace identifier",
    )
    owner_user_id: str | None = Field(
        default=None,
        description="Assigned owner user identifier",
    )
    team_id: str | None = Field(
        default=None,
        description="Assigned operational team identifier",
    )
    domain_id: str | None = Field(
        default=None,
        description="Assigned domain identifier",
    )


class SourceCreate(SourceBase):
    """Schema for creating a new source."""

    @field_validator("config")
    @classmethod
    def validate_config(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate configuration has required fields."""
        if not v:
            raise ValueError("Config cannot be empty")
        return v


class SourceUpdate(BaseSchema):
    """Schema for updating an existing source."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="New source name",
    )
    config: dict[str, Any] | None = Field(
        default=None,
        description="New source configuration",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="New description",
    )
    environment: str | None = Field(
        default=None,
        description="Deployment environment",
    )
    is_active: bool | None = Field(
        default=None,
        description="Whether source is active",
    )


def _contains_redacted(value: Any) -> bool:
    if isinstance(value, dict):
        if value.get("_redacted"):
            return True
        return any(_contains_redacted(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_redacted(child) for child in value)
    return False


class SourceResponse(SourceBase, IDMixin, TimestampMixin):
    """Schema for source responses."""

    is_active: bool = Field(default=True, description="Whether source is active")
    last_validated_at: datetime | None = Field(
        default=None,
        description="Last validation timestamp",
    )
    config_version: int = Field(default=1, description="Config revision number")
    credential_updated_at: datetime | None = Field(
        default=None,
        description="Last credential rotation time",
    )
    has_stored_secrets: bool = Field(
        default=False,
        description="Whether the source contains redacted secret fields",
    )
    owner_user_id: str | None = Field(default=None, description="Owner user identifier")
    owner_name: str | None = Field(default=None, description="Owner user display name")
    team_id: str | None = Field(default=None, description="Owning team identifier")
    team_name: str | None = Field(default=None, description="Owning team display name")
    domain_id: str | None = Field(default=None, description="Owning domain identifier")
    domain_name: str | None = Field(default=None, description="Owning domain display name")

    # Computed properties from relationships
    has_schema: bool = Field(default=False, description="Whether schema exists")
    latest_validation_status: str | None = Field(
        default=None,
        description="Status of latest validation",
    )

    @classmethod
    def from_model(cls, source: Any) -> SourceResponse:
        """Create response from model with computed fields.

        Args:
            source: Source model instance.

        Returns:
            SourceResponse with computed fields.
        """
        redacted_config = redact_config(source.config or {})
        return cls(
            id=source.id,
            name=source.name,
            type=source.type,
            config=redacted_config,
            description=source.description,
            environment=getattr(source, "environment", "production"),
            workspace_id=getattr(source, "workspace_id", None),
            owner_user_id=getattr(source, "owner_user_id", None),
            team_id=getattr(source, "team_id", None),
            domain_id=getattr(source, "domain_id", None),
            is_active=source.is_active,
            created_at=source.created_at,
            updated_at=source.updated_at,
            last_validated_at=source.last_validated_at,
            config_version=getattr(source, "config_version", 1),
            credential_updated_at=getattr(source, "credential_updated_at", None),
            has_stored_secrets=_contains_redacted(redacted_config),
            has_schema=source.latest_schema is not None,
            latest_validation_status=(
                source.latest_validation.status if source.latest_validation else None
            ),
            owner_name=getattr(source, "owner_name", None),
            team_name=getattr(source, "team_name", None),
            domain_name=getattr(source, "domain_name", None),
        )


class SourceListResponse(ListResponseWrapper[SourceResponse]):
    """Paginated source list response."""

    pass


class SourceSummary(BaseSchema):
    """Minimal source summary for lists."""

    id: str
    name: str
    type: SourceType
    is_active: bool
    last_validated_at: datetime | None = None


# =============================================================================
# Source Type Definition Schemas (for dynamic form rendering)
# =============================================================================


class FieldOption(BaseSchema):
    """Option for select/multi-select fields."""

    value: str
    label: str


class FieldDefinitionSchema(BaseSchema):
    """Definition of a configuration field for dynamic form rendering."""

    name: str = Field(..., description="Field identifier")
    label: str = Field(..., description="Display label")
    type: FieldType = Field(default="text", description="Input field type")
    required: bool = Field(default=False, description="Whether field is required")
    placeholder: str = Field(default="", description="Input placeholder text")
    description: str = Field(default="", description="Help text for the field")
    default: Any = Field(default=None, description="Default value")
    options: list[FieldOption] | None = Field(
        default=None,
        description="Options for select fields",
    )
    min_value: int | None = Field(default=None, description="Minimum value for numbers")
    max_value: int | None = Field(default=None, description="Maximum value for numbers")
    depends_on: str | None = Field(
        default=None,
        description="Field this depends on for conditional rendering",
    )
    depends_value: Any = Field(
        default=None,
        description="Value of depends_on field that enables this field",
    )


class SourceTypeDefinitionSchema(BaseSchema):
    """Complete definition of a source type for dynamic form rendering."""

    type: SourceType = Field(..., description="Source type identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Type description")
    icon: str = Field(..., description="Icon identifier for UI")
    category: SourceCategory = Field(..., description="Source category")
    fields: list[FieldDefinitionSchema] = Field(
        ...,
        description="Configuration fields",
    )
    required_fields: list[str] = Field(
        default_factory=list,
        description="List of required field names",
    )
    optional_fields: list[str] = Field(
        default_factory=list,
        description="List of optional field names",
    )
    docs_url: str = Field(default="", description="Documentation URL")


class SourceTypeCategorySchema(BaseSchema):
    """Category for grouping source types."""

    value: str = Field(..., description="Category identifier")
    label: str = Field(..., description="Display label")
    description: str = Field(default="", description="Category description")


class SourceTypesResponse(BaseSchema):
    """Response containing all source types and categories."""

    types: list[SourceTypeDefinitionSchema] = Field(
        ...,
        description="All available source types",
    )
    categories: list[SourceTypeCategorySchema] = Field(
        ...,
        description="Source type categories",
    )


class TestConnectionRequest(BaseSchema):
    """Request to test a source connection before creating."""

    type: SourceType = Field(..., description="Source type")
    config: dict[str, Any] = Field(..., description="Connection configuration")


class SourceCredentialUpdate(BaseSchema):
    """Secret-only credential rotation payload."""

    credentials: dict[str, Any] = Field(
        ...,
        description="Credential fields to rotate",
        examples=[{"password": "new-secret"}],
    )


class TeamResponse(BaseSchema, IDMixin, TimestampMixin):
    workspace_id: str
    name: str
    slug: str
    description: str | None = None
    is_active: bool = True


class TeamCreate(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)


class DomainResponse(BaseSchema, IDMixin, TimestampMixin):
    workspace_id: str
    name: str
    slug: str
    description: str | None = None
    is_active: bool = True


class DomainCreate(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)


class SourceOwnershipResponse(BaseSchema, IDMixin, TimestampMixin):
    source_id: str
    workspace_id: str
    owner_user_id: str | None = None
    owner_name: str | None = None
    team_id: str | None = None
    team_name: str | None = None
    domain_id: str | None = None
    domain_name: str | None = None

    @classmethod
    def from_model(cls, ownership: Any) -> "SourceOwnershipResponse":
        return cls(
            id=ownership.id,
            source_id=ownership.source_id,
            workspace_id=ownership.workspace_id,
            owner_user_id=ownership.owner_user_id,
            owner_name=ownership.owner_user.display_name if ownership.owner_user else None,
            team_id=ownership.team_id,
            team_name=ownership.team.name if ownership.team else None,
            domain_id=ownership.domain_id,
            domain_name=ownership.domain.name if ownership.domain else None,
            created_at=ownership.created_at,
            updated_at=ownership.updated_at,
        )


class SourceOwnershipUpdate(BaseSchema):
    owner_user_id: str | None = None
    team_id: str | None = None
    domain_id: str | None = None


class TestConnectionResponse(BaseSchema):
    """Response from connection test."""

    connected: bool = Field(..., description="Whether connection was successful")
    message: str | None = Field(default=None, description="Success message")
    error: str | None = Field(default=None, description="Error message if failed")
