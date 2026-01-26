"""Base interfaces and types for truthound-dashboard.

This module defines foundational types and interfaces that are used
across all other interface modules. It provides the common building
blocks for the dashboard's abstraction layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Protocol, Union, runtime_checkable


# Type alias for data input - can be path string, DataSource, or DataFrame
DataInput = Union[str, Any]


class DataSourceCapability(Enum):
    """Capabilities that a data source may support.

    This enum defines features that data sources can declare to enable
    optimizations and feature detection.
    """

    LAZY_EVALUATION = auto()  # Supports lazy/deferred execution
    SQL_PUSHDOWN = auto()  # Can push operations to database
    SAMPLING = auto()  # Supports data sampling
    STREAMING = auto()  # Supports streaming processing
    SCHEMA_INFERENCE = auto()  # Can infer schema automatically
    ROW_COUNT = auto()  # Can efficiently count rows
    CONNECTION_TEST = auto()  # Supports connection testing
    WRITE = auto()  # Supports writing data
    TRANSACTION = auto()  # Supports transactions
    BATCH_INSERT = auto()  # Supports batch insert
    UPSERT = auto()  # Supports upsert operations


class ColumnType(str, Enum):
    """Logical column types for schema definition."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    DECIMAL = "decimal"
    BINARY = "binary"
    JSON = "json"
    ARRAY = "array"
    STRUCT = "struct"
    UNKNOWN = "unknown"


@dataclass
class ExecutionContext:
    """Context for execution operations.

    Provides runtime context for validation, profiling, and other
    operations. Includes configuration, environment, and metadata.

    Attributes:
        run_id: Unique execution identifier.
        user_id: User who initiated the execution.
        session_id: Session identifier.
        environment: Environment variables (may contain secrets).
        metadata: Additional metadata.
        tags: Tags for categorization.
        timeout_seconds: Execution timeout.
        parallel: Enable parallel execution.
        max_workers: Max parallel workers.
    """

    run_id: str = ""
    user_id: str | None = None
    session_id: str | None = None
    environment: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 300
    parallel: bool = False
    max_workers: int = 4

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (excluding secrets)."""
        return {
            "run_id": self.run_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "metadata": self.metadata,
            "tags": self.tags,
            "timeout_seconds": self.timeout_seconds,
            "parallel": self.parallel,
            "max_workers": self.max_workers,
        }


@runtime_checkable
class DataSourceProtocol(Protocol):
    """Protocol for data source objects.

    Any object that provides access to tabular data should implement
    this interface. This abstracts away the specific DataSource
    implementation from truthound or other libraries.
    """

    @property
    def name(self) -> str:
        """Get the data source name."""
        ...

    @property
    def columns(self) -> list[str]:
        """Get list of column names."""
        ...

    @property
    def row_count(self) -> int | None:
        """Get row count if available."""
        ...

    @property
    def capabilities(self) -> set[DataSourceCapability]:
        """Get the capabilities of this data source."""
        ...

    def to_polars_lazyframe(self) -> Any:
        """Convert to Polars LazyFrame for processing."""
        ...


@runtime_checkable
class ResultProtocol(Protocol):
    """Protocol for result objects.

    All result types should implement this base protocol for
    consistent serialization and access.
    """

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        ...


@dataclass
class ColumnSchema:
    """Schema definition for a single column.

    Attributes:
        name: Column name.
        dtype: Data type.
        nullable: Whether null values are allowed.
        unique: Whether values must be unique.
        min_value: Minimum value (for numeric/date).
        max_value: Maximum value (for numeric/date).
        allowed_values: Set of allowed values (for categorical).
        pattern: Regex pattern (for string).
        min_length: Minimum string length.
        max_length: Maximum string length.
        description: Column description.
        metadata: Additional metadata.
    """

    name: str
    dtype: ColumnType = ColumnType.UNKNOWN
    nullable: bool = True
    unique: bool = False
    min_value: Any | None = None
    max_value: Any | None = None
    allowed_values: list[Any] | None = None
    pattern: str | None = None
    min_length: int | None = None
    max_length: int | None = None
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "dtype": self.dtype.value,
            "nullable": self.nullable,
            "unique": self.unique,
        }
        if self.min_value is not None:
            result["min_value"] = self.min_value
        if self.max_value is not None:
            result["max_value"] = self.max_value
        if self.allowed_values:
            result["allowed_values"] = self.allowed_values
        if self.pattern:
            result["pattern"] = self.pattern
        if self.min_length is not None:
            result["min_length"] = self.min_length
        if self.max_length is not None:
            result["max_length"] = self.max_length
        if self.description:
            result["description"] = self.description
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class TableSchema:
    """Schema definition for a table/dataset.

    Attributes:
        name: Table/dataset name.
        columns: Column schemas.
        primary_key: Primary key column(s).
        version: Schema version.
        description: Table description.
        metadata: Additional metadata.
    """

    name: str = ""
    columns: list[ColumnSchema] = field(default_factory=list)
    primary_key: list[str] = field(default_factory=list)
    version: str = "1.0"
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_column(self, name: str) -> ColumnSchema | None:
        """Get column schema by name."""
        for col in self.columns:
            if col.name == name:
                return col
        return None

    @property
    def column_names(self) -> list[str]:
        """Get list of column names."""
        return [col.name for col in self.columns]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "columns": [col.to_dict() for col in self.columns],
            "primary_key": self.primary_key,
            "version": self.version,
            "description": self.description,
            "metadata": self.metadata,
        }
