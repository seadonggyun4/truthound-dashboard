"""Base validator schema definitions.

This module defines the core types and enums used across all validator categories.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ValidatorCategory(str, Enum):
    """Validator categories matching truthound's classification.

    Categories are organized by validation purpose:
    - Core validators: schema, completeness, uniqueness, distribution
    - Format validators: string, datetime
    - Statistical validators: aggregate, anomaly, drift
    - Relational validators: cross_table, multi_column, query
    - Domain validators: table, geospatial, privacy, business
    - Advanced validators: time_series, referential, streaming
    """

    # Core validators (no extra dependencies)
    SCHEMA = "schema"
    COMPLETENESS = "completeness"
    UNIQUENESS = "uniqueness"
    DISTRIBUTION = "distribution"

    # Format validators
    STRING = "string"
    DATETIME = "datetime"

    # Statistical validators
    AGGREGATE = "aggregate"
    ANOMALY = "anomaly"  # requires: anomaly (scipy + sklearn)
    DRIFT = "drift"  # requires: drift (scipy)

    # Relational validators
    CROSS_TABLE = "cross_table"
    MULTI_COLUMN = "multi_column"
    QUERY = "query"

    # Domain validators
    TABLE = "table"
    GEOSPATIAL = "geospatial"
    PRIVACY = "privacy"
    BUSINESS = "business"

    # Advanced validators
    TIME_SERIES = "time_series"
    REFERENTIAL = "referential"
    STREAMING = "streaming"


class ParameterType(str, Enum):
    """Supported parameter types for validator configuration."""

    STRING = "string"
    STRING_LIST = "string_list"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    SELECT = "select"  # Single selection from options
    MULTI_SELECT = "multi_select"  # Multiple selections
    COLUMN = "column"  # Column name from data source
    COLUMN_LIST = "column_list"  # Multiple column names
    SCHEMA = "schema"  # JSON/YAML schema definition
    EXPRESSION = "expression"  # Polars expression string
    REGEX = "regex"  # Regular expression pattern
    DATE = "date"  # Date value (YYYY-MM-DD)
    DATETIME = "datetime"  # Datetime value
    SOURCE_REF = "source_ref"  # Reference to another data source


class ParameterDefinition(BaseModel):
    """Definition of a validator parameter."""

    name: str = Field(..., description="Parameter name (matches truthound API)")
    label: str = Field(..., description="Display label for UI")
    type: ParameterType = Field(..., description="Parameter type")
    description: str = Field(default="", description="Help text for the parameter")
    required: bool = Field(default=False, description="Whether parameter is required")
    default: Any = Field(default=None, description="Default value if not specified")
    options: list[dict[str, str]] | None = Field(
        default=None,
        description="Options for select/multi_select types [{value, label}]",
    )
    min_value: float | None = Field(default=None, description="Minimum for numeric types")
    max_value: float | None = Field(default=None, description="Maximum for numeric types")
    placeholder: str | None = Field(default=None, description="Placeholder text")
    validation_pattern: str | None = Field(
        default=None, description="Regex pattern for validation"
    )
    depends_on: str | None = Field(
        default=None,
        description="Parameter name this depends on (for conditional display)",
    )
    depends_value: Any = Field(
        default=None,
        description="Value the dependency must have for this param to show",
    )
    group: str | None = Field(
        default=None,
        description="Parameter group for UI organization",
    )


class ValidatorDefinition(BaseModel):
    """Complete definition of a validator including its parameters."""

    name: str = Field(..., description="Validator class name (e.g., 'ColumnExists')")
    display_name: str = Field(..., description="Human-readable name")
    category: ValidatorCategory = Field(..., description="Validator category")
    description: str = Field(..., description="What this validator checks")
    parameters: list[ParameterDefinition] = Field(
        default_factory=list, description="Configurable parameters"
    )
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
    severity_default: Literal["low", "medium", "high", "critical"] = Field(
        default="medium", description="Default issue severity"
    )
    requires_extra: str | None = Field(
        default=None,
        description="Extra dependency required (e.g., 'drift', 'anomaly')",
    )
    experimental: bool = Field(
        default=False,
        description="Whether this validator is experimental",
    )
    deprecated: bool = Field(
        default=False,
        description="Whether this validator is deprecated",
    )
    deprecation_message: str | None = Field(
        default=None,
        description="Message explaining deprecation and alternatives",
    )


class ValidatorConfig(BaseModel):
    """Configuration for running a specific validator with parameters."""

    name: str = Field(..., description="Validator name")
    enabled: bool = Field(default=True, description="Whether to run this validator")
    params: dict[str, Any] = Field(
        default_factory=dict, description="Parameter values"
    )
    severity_override: Literal["low", "medium", "high", "critical"] | None = Field(
        default=None, description="Override default severity"
    )


class ValidatorConfigList(BaseModel):
    """List of validator configurations for a validation run."""

    validators: list[ValidatorConfig] = Field(
        default_factory=list, description="Configured validators"
    )


# ============================================================================
# Validator Config Conversion Utilities
# ============================================================================


def configs_to_truthound_format(
    configs: list[ValidatorConfig],
) -> tuple[list[str] | None, dict[str, dict[str, Any]]]:
    """Convert ValidatorConfig list to truthound-compatible format.

    truthound supports two ways of specifying validators:
    1. Simple list of validator names: validators=["Null", "Duplicate"]
    2. Dict-based configuration: validator_params={"Null": {"columns": ["a", "b"]}}

    This function converts our ValidatorConfig format to both formats,
    allowing the caller to choose based on whether custom params exist.

    Args:
        configs: List of ValidatorConfig objects from API request.

    Returns:
        Tuple of (validator_names, validator_params):
        - validator_names: List of enabled validator names, or None if empty
        - validator_params: Dict of {validator_name: {param: value}} for
          validators with non-default parameters

    Example:
        >>> configs = [
        ...     ValidatorConfig(name="Null", enabled=True, params={"columns": ["a"]}),
        ...     ValidatorConfig(name="Duplicate", enabled=True, params={}),
        ...     ValidatorConfig(name="Range", enabled=False, params={}),
        ... ]
        >>> names, params = configs_to_truthound_format(configs)
        >>> names
        ['Null', 'Duplicate']
        >>> params
        {'Null': {'columns': ['a']}}
    """
    enabled_names: list[str] = []
    validator_params: dict[str, dict[str, Any]] = {}

    for config in configs:
        if not config.enabled:
            continue

        enabled_names.append(config.name)

        # Only include params that are non-empty
        if config.params:
            # Filter out None, empty strings, and empty lists
            filtered_params = {
                k: v
                for k, v in config.params.items()
                if v is not None and v != "" and v != []
            }
            if filtered_params:
                validator_params[config.name] = filtered_params

    return enabled_names if enabled_names else None, validator_params


def has_custom_params(configs: list[ValidatorConfig]) -> bool:
    """Check if any configs have custom (non-default) parameters.

    This helps determine whether to use simple or advanced mode when
    calling truthound.

    Args:
        configs: List of ValidatorConfig objects.

    Returns:
        True if at least one enabled config has non-empty params.
    """
    for config in configs:
        if not config.enabled:
            continue
        if config.params:
            # Check for any non-empty param values
            for value in config.params.values():
                if value is not None and value != "" and value != []:
                    return True
    return False


def merge_severity_overrides(
    configs: list[ValidatorConfig],
) -> dict[str, str]:
    """Extract severity overrides from configs.

    Args:
        configs: List of ValidatorConfig objects.

    Returns:
        Dict mapping validator names to their severity overrides.
    """
    return {
        config.name: config.severity_override
        for config in configs
        if config.enabled and config.severity_override is not None
    }
