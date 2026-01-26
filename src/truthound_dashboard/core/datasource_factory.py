"""DataSource factory for truthound datasources.

This module provides a unified interface to create truthound DataSource objects
from various backend types (files, SQL databases, cloud warehouses, etc.).

The factory pattern allows the dashboard to support multiple data backends
through the truthound datasources API while maintaining a consistent interface
for services. The design prioritizes loose coupling with truthound for
maintainability and testability.

Architecture:
    SourceConfig -> DataSourceFactory -> truthound.datasources.*

Updated for truthound 2.x API:
    - Uses truthound.datasources.get_datasource() for auto-detection
    - Uses SQLDataSourceConfig for SQL sources
    - Uses DataSourceCapability for feature detection

Supported Data Sources:
    - File: CSV, Parquet, JSON, NDJSON, JSONL
    - DataFrame: Polars, Pandas
    - SQL: SQLite, PostgreSQL, MySQL, DuckDB
    - Cloud DW: BigQuery, Snowflake, Redshift, Databricks
    - Enterprise: Oracle, SQL Server
    - NoSQL: MongoDB, Elasticsearch (async)
    - Streaming: Kafka (async)

Example:
    factory = DataSourceFactory()
    source = factory.create_from_config(source_config)
    report = th.check(source=source)

    # Or use the get_datasource convenience function
    from truthound.datasources import get_datasource
    ds = get_datasource("data.csv")  # Auto-detect file type
    ds = get_datasource("postgresql://user:pass@localhost/db", table="users")
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# =============================================================================
# Source Type Enumeration
# =============================================================================


class SourceType(str, Enum):
    """Supported data source types."""

    # File-based
    FILE = "file"
    CSV = "csv"
    PARQUET = "parquet"
    JSON = "json"
    NDJSON = "ndjson"
    JSONL = "jsonl"

    # DataFrame
    POLARS = "polars"
    PANDAS = "pandas"

    # Core SQL
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    DUCKDB = "duckdb"

    # Cloud Data Warehouses
    BIGQUERY = "bigquery"
    SNOWFLAKE = "snowflake"
    REDSHIFT = "redshift"
    DATABRICKS = "databricks"

    # Enterprise
    ORACLE = "oracle"
    SQLSERVER = "sqlserver"

    # NoSQL (async)
    MONGODB = "mongodb"
    ELASTICSEARCH = "elasticsearch"

    # Streaming (async)
    KAFKA = "kafka"

    @classmethod
    def is_file_type(cls, source_type: str) -> bool:
        """Check if source type is file-based."""
        file_types = {
            cls.FILE,
            cls.CSV,
            cls.PARQUET,
            cls.JSON,
            cls.NDJSON,
            cls.JSONL,
        }
        try:
            return cls(source_type) in file_types
        except ValueError:
            return False

    @classmethod
    def is_sql_type(cls, source_type: str) -> bool:
        """Check if source type is SQL-based."""
        sql_types = {
            cls.SQLITE,
            cls.POSTGRESQL,
            cls.MYSQL,
            cls.DUCKDB,
            cls.BIGQUERY,
            cls.SNOWFLAKE,
            cls.REDSHIFT,
            cls.DATABRICKS,
            cls.ORACLE,
            cls.SQLSERVER,
        }
        try:
            return cls(source_type) in sql_types
        except ValueError:
            return False

    @classmethod
    def is_async_type(cls, source_type: str) -> bool:
        """Check if source type requires async operations."""
        async_types = {
            cls.MONGODB,
            cls.ELASTICSEARCH,
            cls.KAFKA,
        }
        try:
            return cls(source_type) in async_types
        except ValueError:
            return False


# =============================================================================
# Source Configuration
# =============================================================================


@dataclass
class SourceConfig:
    """Configuration for creating a data source.

    This dataclass holds all possible configuration options for any
    data source type. Only relevant fields are used based on source_type.

    Attributes:
        source_type: Type of data source (file, postgresql, etc.)
        name: Human-readable name for the source.

        # File-based options
        path: File path for file-based sources.

        # SQL options
        table: Table name for SQL sources.
        query: Custom SQL query (alternative to table).
        host: Database host.
        port: Database port.
        database: Database name.
        schema_name: Database schema (e.g., "public" for PostgreSQL).
        user: Database username.
        password: Database password.
        connection_string: Full connection string (alternative to individual params).

        # Cloud DW specific
        project: GCP project ID (BigQuery).
        dataset: BigQuery dataset name.
        account: Snowflake account identifier.
        warehouse: Snowflake warehouse name.
        credentials_path: Path to credentials file (BigQuery).
        access_token: Access token (Databricks).
        http_path: HTTP path for SQL warehouse (Databricks).
        catalog: Unity Catalog name (Databricks).
        cluster_identifier: Redshift cluster ID.
        iam_auth: Use IAM authentication (Redshift).

        # Enterprise DB specific
        service_name: Oracle service name.
        sid: Oracle SID.
        trusted_connection: Windows auth (SQL Server).

        # NoSQL specific
        collection: MongoDB collection name.
        index: Elasticsearch index name.

        # Streaming specific
        topic: Kafka topic name.
        bootstrap_servers: Kafka bootstrap servers.
        group_id: Kafka consumer group ID.

        # General options
        pool_size: Connection pool size.
        query_timeout: Query timeout in seconds.
        max_rows: Maximum rows to fetch.
        sample_size: Sample size for large datasets.
    """

    source_type: str
    name: str | None = None

    # File-based
    path: str | None = None

    # SQL common
    table: str | None = None
    query: str | None = None
    host: str | None = None
    port: int | None = None
    database: str | None = None
    schema_name: str | None = None
    user: str | None = None
    password: str | None = None
    connection_string: str | None = None

    # Cloud DW
    project: str | None = None
    dataset: str | None = None
    account: str | None = None
    warehouse: str | None = None
    credentials_path: str | None = None
    access_token: str | None = None
    http_path: str | None = None
    catalog: str | None = None
    cluster_identifier: str | None = None
    iam_auth: bool = False

    # Enterprise
    service_name: str | None = None
    sid: str | None = None
    trusted_connection: bool = False

    # NoSQL
    collection: str | None = None
    index: str | None = None

    # Streaming
    topic: str | None = None
    bootstrap_servers: str | None = None
    group_id: str | None = None
    max_messages: int | None = None

    # General
    pool_size: int | None = None
    query_timeout: float | None = None
    max_rows: int | None = None
    sample_size: int | None = None

    # Extra options (for extensibility)
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceConfig":
        """Create SourceConfig from dictionary.

        Args:
            data: Dictionary with source configuration.
                Must include 'type' or 'source_type' key.

        Returns:
            SourceConfig instance.

        Raises:
            ValueError: If source_type is missing.
        """
        # Handle 'type' as alias for 'source_type'
        source_type = data.get("source_type") or data.get("type")
        if not source_type:
            raise ValueError("source_type or type is required")

        # Extract known fields
        known_fields = {
            "name",
            "path",
            "table",
            "query",
            "host",
            "port",
            "database",
            "schema_name",
            "user",
            "password",
            "connection_string",
            "project",
            "dataset",
            "account",
            "warehouse",
            "credentials_path",
            "access_token",
            "http_path",
            "catalog",
            "cluster_identifier",
            "iam_auth",
            "service_name",
            "sid",
            "trusted_connection",
            "collection",
            "index",
            "topic",
            "bootstrap_servers",
            "group_id",
            "max_messages",
            "pool_size",
            "query_timeout",
            "max_rows",
            "sample_size",
        }

        kwargs: dict[str, Any] = {"source_type": source_type}
        extra: dict[str, Any] = {}

        for key, value in data.items():
            if key in ("type", "source_type"):
                continue
            if key in known_fields:
                kwargs[key] = value
            else:
                extra[key] = value

        if extra:
            kwargs["extra"] = extra

        return cls(**kwargs)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result: dict[str, Any] = {"type": self.source_type}

        # Add non-None fields
        for key in [
            "name",
            "path",
            "table",
            "query",
            "host",
            "port",
            "database",
            "schema_name",
            "user",
            "password",
            "connection_string",
            "project",
            "dataset",
            "account",
            "warehouse",
            "credentials_path",
            "access_token",
            "http_path",
            "catalog",
            "cluster_identifier",
            "service_name",
            "sid",
            "collection",
            "index",
            "topic",
            "bootstrap_servers",
            "group_id",
            "max_messages",
            "pool_size",
            "query_timeout",
            "max_rows",
            "sample_size",
        ]:
            value = getattr(self, key)
            if value is not None:
                result[key] = value

        # Add boolean flags if True
        if self.iam_auth:
            result["iam_auth"] = True
        if self.trusted_connection:
            result["trusted_connection"] = True

        # Add extra
        if self.extra:
            result.update(self.extra)

        return result


# =============================================================================
# DataSource Protocol (for loose coupling)
# =============================================================================


@runtime_checkable
class DataSourceProtocol(Protocol):
    """Protocol for truthound DataSource objects.

    This protocol defines the interface that all DataSource implementations
    must satisfy. It's used for type checking and loose coupling.
    """

    @property
    def name(self) -> str:
        """Get source name."""
        ...

    @property
    def schema(self) -> dict[str, Any]:
        """Get schema dictionary."""
        ...

    @property
    def columns(self) -> list[str]:
        """Get column names."""
        ...

    @property
    def row_count(self) -> int | None:
        """Get row count if available."""
        ...

    def to_polars_lazyframe(self) -> Any:
        """Convert to Polars LazyFrame."""
        ...


# =============================================================================
# Backend Strategy Pattern (for extensibility)
# =============================================================================


class DataSourceCreator(ABC):
    """Abstract base class for data source creators.

    Each data source type has its own creator class that handles
    the specific logic for creating that type of source.
    """

    @abstractmethod
    def can_create(self, config: SourceConfig) -> bool:
        """Check if this creator can handle the given config."""
        ...

    @abstractmethod
    def create(self, config: SourceConfig) -> Any:
        """Create the data source from config."""
        ...


class FileSourceCreator(DataSourceCreator):
    """Creator for file-based data sources.

    Updated for truthound 2.x API:
    - Uses truthound.datasources.polars_source.FileDataSource
    - Supports FileDataSourceConfig for advanced options
    """

    def can_create(self, config: SourceConfig) -> bool:
        return SourceType.is_file_type(config.source_type)

    def create(self, config: SourceConfig) -> Any:
        """Create file-based data source using truthound's FileDataSource."""
        if not config.path:
            raise ValueError("path is required for file sources")

        path = Path(config.path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {config.path}")

        try:
            # Try new truthound 2.x API first
            from truthound.datasources.polars_source import (
                FileDataSource,
                FileDataSourceConfig,
            )

            # Build config if extra options provided
            file_config = None
            if config.extra:
                file_config = FileDataSourceConfig(
                    infer_schema_length=config.extra.get("infer_schema_length", 10000),
                    ignore_errors=config.extra.get("ignore_errors", False),
                    encoding=config.extra.get("encoding", "utf8"),
                    separator=config.extra.get("separator", ","),
                )
                return FileDataSource(str(path), config=file_config)

            return FileDataSource(str(path))

        except ImportError:
            try:
                # Fallback: Try older truthound.datasources.FileDataSource
                from truthound.datasources import FileDataSource
                return FileDataSource(str(path))
            except ImportError:
                # Final fallback: return path string (backward compatible)
                # truthound core functions also accept path strings
                logger.debug("truthound.datasources not available, using path string")
                return str(path)


class SQLiteSourceCreator(DataSourceCreator):
    """Creator for SQLite data sources.

    Updated for truthound 2.x API:
    - Uses truthound.datasources.sql.sqlite.SQLiteDataSource
    - Supports SQLiteDataSourceConfig for advanced options
    """

    def can_create(self, config: SourceConfig) -> bool:
        return config.source_type.lower() == SourceType.SQLITE

    def create(self, config: SourceConfig) -> Any:
        if not config.database and not config.path:
            raise ValueError("database or path is required for SQLite")

        database = config.database or config.path

        try:
            # Try new truthound 2.x API with explicit import path
            from truthound.datasources.sql.sqlite import (
                SQLiteDataSource,
                SQLiteDataSourceConfig,
            )

            # Build config if extra options provided
            sqlite_config = None
            if config.extra or config.query_timeout:
                sqlite_config = SQLiteDataSourceConfig(
                    database=database,
                    timeout=config.query_timeout or 5.0,
                )

            if config.table:
                if sqlite_config:
                    return SQLiteDataSource(table=config.table, database=database, config=sqlite_config)
                return SQLiteDataSource(table=config.table, database=database)
            elif config.query:
                if sqlite_config:
                    return SQLiteDataSource(query=config.query, database=database, config=sqlite_config)
                return SQLiteDataSource(query=config.query, database=database)
            else:
                raise ValueError("table or query is required for SQLite")

        except ImportError:
            # Fallback: Try older import path
            from truthound.datasources.sql import SQLiteDataSource

            if config.table:
                return SQLiteDataSource(table=config.table, database=database)
            elif config.query:
                return SQLiteDataSource(query=config.query, database=database)
            else:
                raise ValueError("table or query is required for SQLite")


class DuckDBSourceCreator(DataSourceCreator):
    """Creator for DuckDB data sources.

    Note: DuckDB support depends on truthound's optional DuckDB backend.
    If not available, falls back to direct Polars reading.
    """

    def can_create(self, config: SourceConfig) -> bool:
        return config.source_type.lower() == SourceType.DUCKDB

    def create(self, config: SourceConfig) -> Any:
        if not config.database and not config.path:
            raise ValueError("database or path is required for DuckDB")

        database = config.database or config.path

        # Try truthound's DuckDB support first
        try:
            from truthound.datasources.sql import DuckDBDataSource

            if config.table:
                return DuckDBDataSource(table=config.table, database=database)
            elif config.query:
                return DuckDBDataSource(query=config.query, database=database)
            else:
                raise ValueError("table or query is required for DuckDB")

        except ImportError:
            # Fallback: Use Polars to read from DuckDB directly
            logger.debug("truthound DuckDB not available, using Polars fallback")
            try:
                import polars as pl

                if not config.table and not config.query:
                    raise ValueError("table or query is required for DuckDB")

                query = config.query or f"SELECT * FROM {config.table}"
                # Use read_database_uri for DuckDB connections
                try:
                    df = pl.read_database_uri(query, f"duckdb:///{database}")
                except Exception as read_err:
                    raise ImportError(
                        f"Failed to read from DuckDB: {read_err}. "
                        "Install DuckDB connector with: pip install duckdb connectorx"
                    ) from read_err

                # Return as PolarsDataSource for consistency
                from truthound.datasources import PolarsDataSource
                return PolarsDataSource(df, name=config.name or database)

            except ImportError as ie:
                raise ImportError(
                    f"DuckDB support requires additional packages. {ie}"
                ) from ie


class PostgreSQLSourceCreator(DataSourceCreator):
    """Creator for PostgreSQL data sources.

    Updated for truthound 2.x API:
    - Uses truthound.datasources.sql.postgresql.PostgreSQLDataSource
    - Supports PostgreSQLDataSourceConfig for advanced options including:
      - sslmode, application_name, pool_size, query_timeout
    """

    def can_create(self, config: SourceConfig) -> bool:
        return config.source_type.lower() == SourceType.POSTGRESQL

    def create(self, config: SourceConfig) -> Any:
        try:
            # Try new truthound 2.x API with explicit import path
            from truthound.datasources.sql.postgresql import (
                PostgreSQLDataSource,
                PostgreSQLDataSourceConfig,
            )

            # Use connection string if provided
            if config.connection_string:
                if not config.table and not config.query:
                    raise ValueError("table or query is required")
                return PostgreSQLDataSource.from_connection_string(
                    connection_string=config.connection_string,
                    table=config.table,
                    query=config.query,
                    schema_name=config.schema_name,
                )

            # Use individual parameters
            if not config.host or not config.database:
                raise ValueError("host and database are required for PostgreSQL")

            # Build PostgreSQLDataSourceConfig for advanced options
            pg_config = PostgreSQLDataSourceConfig(
                host=config.host,
                port=config.port or 5432,
                database=config.database,
                user=config.user or "postgres",
                password=config.password,
                sslmode=config.extra.get("sslmode", "prefer") if config.extra else "prefer",
                application_name=config.extra.get("application_name", "truthound-dashboard") if config.extra else "truthound-dashboard",
                schema_name=config.schema_name or "public",
                pool_size=config.pool_size or 10,
                query_timeout=config.query_timeout or 300.0,
            )

            if config.table:
                return PostgreSQLDataSource(table=config.table, config=pg_config)
            elif config.query:
                return PostgreSQLDataSource(query=config.query, config=pg_config)
            else:
                raise ValueError("table or query is required")

        except ImportError:
            # Fallback: Try older import path
            from truthound.datasources.sql import PostgreSQLDataSource

            if config.connection_string:
                if not config.table and not config.query:
                    raise ValueError("table or query is required")
                return PostgreSQLDataSource.from_connection_string(
                    connection_string=config.connection_string,
                    table=config.table,
                    query=config.query,
                    schema_name=config.schema_name,
                )

            if not config.host or not config.database:
                raise ValueError("host and database are required for PostgreSQL")

            kwargs: dict[str, Any] = {
                "host": config.host,
                "database": config.database,
            }

            if config.table:
                kwargs["table"] = config.table
            elif config.query:
                kwargs["query"] = config.query
            else:
                raise ValueError("table or query is required")

            if config.port:
                kwargs["port"] = config.port
            if config.user:
                kwargs["user"] = config.user
            if config.password:
                kwargs["password"] = config.password
            if config.schema_name:
                kwargs["schema_name"] = config.schema_name

            return PostgreSQLDataSource(**kwargs)


class MySQLSourceCreator(DataSourceCreator):
    """Creator for MySQL data sources.

    Updated for truthound 2.x API:
    - Uses truthound.datasources.sql.mysql.MySQLDataSource
    - Supports MySQLDataSourceConfig for advanced options
    """

    def can_create(self, config: SourceConfig) -> bool:
        return config.source_type.lower() == SourceType.MYSQL

    def create(self, config: SourceConfig) -> Any:
        try:
            # Try new truthound 2.x API with explicit import path
            from truthound.datasources.sql.mysql import (
                MySQLDataSource,
                MySQLDataSourceConfig,
            )

            if config.connection_string:
                return MySQLDataSource.from_connection_string(
                    connection_string=config.connection_string,
                    table=config.table,
                )

            if not config.host or not config.database:
                raise ValueError("host and database are required for MySQL")

            # Build MySQLDataSourceConfig for advanced options
            mysql_config = MySQLDataSourceConfig(
                host=config.host,
                port=config.port or 3306,
                database=config.database,
                user=config.user or "root",
                password=config.password,
                charset=config.extra.get("charset", "utf8mb4") if config.extra else "utf8mb4",
                autocommit=config.extra.get("autocommit", True) if config.extra else True,
            )

            if config.table:
                return MySQLDataSource(table=config.table, config=mysql_config)
            elif config.query:
                return MySQLDataSource(query=config.query, config=mysql_config)
            else:
                raise ValueError("table or query is required")

        except ImportError:
            # Fallback: Try older import path
            from truthound.datasources.sql import MySQLDataSource

            if config.connection_string:
                return MySQLDataSource.from_connection_string(
                    connection_string=config.connection_string,
                    table=config.table,
                )

            if not config.host or not config.database:
                raise ValueError("host and database are required for MySQL")

            kwargs: dict[str, Any] = {
                "host": config.host,
                "database": config.database,
            }

            if config.table:
                kwargs["table"] = config.table
            elif config.query:
                kwargs["query"] = config.query
            else:
                raise ValueError("table or query is required")

            if config.port:
                kwargs["port"] = config.port
            if config.user:
                kwargs["user"] = config.user
            if config.password:
                kwargs["password"] = config.password

            return MySQLDataSource(**kwargs)


class BigQuerySourceCreator(DataSourceCreator):
    """Creator for BigQuery data sources.

    Updated for truthound 2.x API:
    - Uses truthound.datasources.sql.bigquery.BigQueryDataSource
    - Supports BigQueryConfig for cost control and advanced options
    """

    def can_create(self, config: SourceConfig) -> bool:
        return config.source_type.lower() == SourceType.BIGQUERY

    def create(self, config: SourceConfig) -> Any:
        if not config.project:
            raise ValueError("project is required for BigQuery")

        try:
            # Try new truthound 2.x API with explicit import path
            from truthound.datasources.sql.bigquery import (
                BigQueryDataSource,
                BigQueryConfig,
            )

            # Build BigQueryConfig for advanced options
            bq_config = BigQueryConfig(
                dataset=config.dataset,
                location=config.extra.get("location") if config.extra else None,
                use_legacy_sql=config.extra.get("use_legacy_sql", False) if config.extra else False,
                maximum_bytes_billed=config.extra.get("maximum_bytes_billed") if config.extra else None,
                job_timeout=config.query_timeout or 300,
            )

            if config.table:
                return BigQueryDataSource(
                    table=config.table,
                    project=config.project,
                    credentials_path=config.credentials_path,
                    config=bq_config,
                )
            elif config.query:
                return BigQueryDataSource(
                    query=config.query,
                    project=config.project,
                    credentials_path=config.credentials_path,
                    config=bq_config,
                )
            else:
                raise ValueError("table or query is required for BigQuery")

        except ImportError:
            # Fallback: Try older import path
            from truthound.datasources.sql import BigQueryDataSource

            kwargs: dict[str, Any] = {"project": config.project}

            if config.dataset:
                kwargs["dataset"] = config.dataset
            if config.table:
                kwargs["table"] = config.table
            elif config.query:
                kwargs["query"] = config.query
            if config.credentials_path:
                kwargs["credentials_path"] = config.credentials_path

            return BigQueryDataSource(**kwargs)


class SnowflakeSourceCreator(DataSourceCreator):
    """Creator for Snowflake data sources.

    Updated for truthound 2.x API:
    - Uses truthound.datasources.sql.snowflake.SnowflakeDataSource
    - Supports SnowflakeConfig for advanced auth options
    """

    def can_create(self, config: SourceConfig) -> bool:
        return config.source_type.lower() == SourceType.SNOWFLAKE

    def create(self, config: SourceConfig) -> Any:
        if not config.account:
            raise ValueError("account is required for Snowflake")

        try:
            # Try new truthound 2.x API with explicit import path
            from truthound.datasources.sql.snowflake import (
                SnowflakeDataSource,
                SnowflakeConfig,
            )

            # Build SnowflakeConfig for advanced options
            sf_config = SnowflakeConfig(
                account=config.account,
                user=config.user,
                password=config.password,
                database=config.database,
                schema_name=config.schema_name or "PUBLIC",
                warehouse=config.warehouse,
                role=config.extra.get("role") if config.extra else None,
                authenticator=config.extra.get("authenticator", "snowflake") if config.extra else "snowflake",
                private_key_path=config.extra.get("private_key_path") if config.extra else None,
                private_key_passphrase=config.extra.get("private_key_passphrase") if config.extra else None,
                client_session_keep_alive=config.extra.get("client_session_keep_alive", True) if config.extra else True,
            )

            if config.table:
                return SnowflakeDataSource(table=config.table, config=sf_config)
            elif config.query:
                return SnowflakeDataSource(query=config.query, config=sf_config)
            else:
                raise ValueError("table or query is required")

        except ImportError:
            # Fallback: Try older import path
            from truthound.datasources.sql import SnowflakeDataSource

            kwargs: dict[str, Any] = {"account": config.account}

            if config.table:
                kwargs["table"] = config.table
            elif config.query:
                kwargs["query"] = config.query
            else:
                raise ValueError("table or query is required")

            if config.database:
                kwargs["database"] = config.database
            if config.schema_name:
                kwargs["schema"] = config.schema_name
            if config.warehouse:
                kwargs["warehouse"] = config.warehouse
            if config.user:
                kwargs["user"] = config.user
            if config.password:
                kwargs["password"] = config.password

            return SnowflakeDataSource(**kwargs)


class RedshiftSourceCreator(DataSourceCreator):
    """Creator for Redshift data sources."""

    def can_create(self, config: SourceConfig) -> bool:
        return config.source_type.lower() == SourceType.REDSHIFT

    def create(self, config: SourceConfig) -> Any:
        from truthound.datasources.sql import RedshiftDataSource

        if not config.host or not config.database:
            raise ValueError("host and database are required for Redshift")

        kwargs: dict[str, Any] = {
            "host": config.host,
            "database": config.database,
        }

        if config.table:
            kwargs["table"] = config.table
        elif config.query:
            kwargs["query"] = config.query
        else:
            raise ValueError("table or query is required")

        if config.port:
            kwargs["port"] = config.port
        if config.user:
            kwargs["user"] = config.user
        if config.password:
            kwargs["password"] = config.password
        if config.schema_name:
            kwargs["schema"] = config.schema_name
        if config.cluster_identifier:
            kwargs["cluster_identifier"] = config.cluster_identifier
        if config.iam_auth:
            kwargs["iam_auth"] = True

        return RedshiftDataSource(**kwargs)


class DatabricksSourceCreator(DataSourceCreator):
    """Creator for Databricks data sources.

    Updated for truthound 2.x API:
    - Uses truthound.datasources.sql.databricks.DatabricksDataSource
    - Supports DatabricksConfig for Unity Catalog and OAuth
    """

    def can_create(self, config: SourceConfig) -> bool:
        return config.source_type.lower() == SourceType.DATABRICKS

    def create(self, config: SourceConfig) -> Any:
        if not config.host or not config.http_path:
            raise ValueError("host and http_path are required for Databricks")

        try:
            # Try new truthound 2.x API with explicit import path
            from truthound.datasources.sql.databricks import (
                DatabricksDataSource,
                DatabricksConfig,
            )

            # Build DatabricksConfig for advanced options
            db_config = DatabricksConfig(
                host=config.host,
                http_path=config.http_path,
                access_token=config.access_token,
                catalog=config.catalog,
                use_cloud_fetch=config.extra.get("use_cloud_fetch", True) if config.extra else True,
                max_download_threads=config.extra.get("max_download_threads", 10) if config.extra else 10,
                client_id=config.extra.get("client_id") if config.extra else None,
                client_secret=config.extra.get("client_secret") if config.extra else None,
                use_oauth=config.extra.get("use_oauth", False) if config.extra else False,
            )

            if config.table:
                return DatabricksDataSource(table=config.table, schema=config.schema_name, config=db_config)
            elif config.query:
                return DatabricksDataSource(query=config.query, config=db_config)
            else:
                raise ValueError("table or query is required")

        except ImportError:
            # Fallback: Try older import path
            from truthound.datasources.sql import DatabricksDataSource

            kwargs: dict[str, Any] = {
                "host": config.host,
                "http_path": config.http_path,
            }

            if config.table:
                kwargs["table"] = config.table
            elif config.query:
                kwargs["query"] = config.query
            else:
                raise ValueError("table or query is required")

            if config.access_token:
                kwargs["access_token"] = config.access_token
            if config.catalog:
                kwargs["catalog"] = config.catalog
            if config.schema_name:
                kwargs["schema"] = config.schema_name

            return DatabricksDataSource(**kwargs)


class OracleSourceCreator(DataSourceCreator):
    """Creator for Oracle data sources."""

    def can_create(self, config: SourceConfig) -> bool:
        return config.source_type.lower() == SourceType.ORACLE

    def create(self, config: SourceConfig) -> Any:
        from truthound.datasources.sql import OracleDataSource

        kwargs: dict[str, Any] = {}

        if config.table:
            kwargs["table"] = config.table
        elif config.query:
            kwargs["query"] = config.query
        else:
            raise ValueError("table or query is required")

        if config.host:
            kwargs["host"] = config.host
        if config.port:
            kwargs["port"] = config.port
        if config.service_name:
            kwargs["service_name"] = config.service_name
        elif config.sid:
            kwargs["sid"] = config.sid
        if config.user:
            kwargs["user"] = config.user
        if config.password:
            kwargs["password"] = config.password

        return OracleDataSource(**kwargs)


class SQLServerSourceCreator(DataSourceCreator):
    """Creator for SQL Server data sources."""

    def can_create(self, config: SourceConfig) -> bool:
        return config.source_type.lower() == SourceType.SQLSERVER

    def create(self, config: SourceConfig) -> Any:
        from truthound.datasources.sql import SQLServerDataSource

        kwargs: dict[str, Any] = {}

        if config.table:
            kwargs["table"] = config.table
        elif config.query:
            kwargs["query"] = config.query
        else:
            raise ValueError("table or query is required")

        if config.host:
            kwargs["host"] = config.host
        if config.port:
            kwargs["port"] = config.port
        if config.database:
            kwargs["database"] = config.database
        if config.user:
            kwargs["user"] = config.user
        if config.password:
            kwargs["password"] = config.password
        if config.schema_name:
            kwargs["schema"] = config.schema_name
        if config.trusted_connection:
            kwargs["trusted_connection"] = True

        return SQLServerDataSource(**kwargs)


# =============================================================================
# Async Source Creators
# =============================================================================


class MongoDBSourceCreator(DataSourceCreator):
    """Creator for MongoDB data sources (async)."""

    def can_create(self, config: SourceConfig) -> bool:
        return config.source_type.lower() == SourceType.MONGODB

    def create(self, config: SourceConfig) -> Any:
        raise ValueError(
            "MongoDB requires async creation. Use create_async() instead."
        )

    async def create_async(self, config: SourceConfig) -> Any:
        from truthound.datasources import from_mongodb

        if not config.connection_string and not config.host:
            raise ValueError("connection_string or host is required for MongoDB")
        if not config.database:
            raise ValueError("database is required for MongoDB")
        if not config.collection:
            raise ValueError("collection is required for MongoDB")

        connection_string = config.connection_string
        if not connection_string:
            connection_string = f"mongodb://{config.host}:{config.port or 27017}"

        return await from_mongodb(
            connection_string=connection_string,
            database=config.database,
            collection=config.collection,
        )


class ElasticsearchSourceCreator(DataSourceCreator):
    """Creator for Elasticsearch data sources (async)."""

    def can_create(self, config: SourceConfig) -> bool:
        return config.source_type.lower() == SourceType.ELASTICSEARCH

    def create(self, config: SourceConfig) -> Any:
        raise ValueError(
            "Elasticsearch requires async creation. Use create_async() instead."
        )

    async def create_async(self, config: SourceConfig) -> Any:
        from truthound.datasources import from_elasticsearch

        if not config.host:
            raise ValueError("host is required for Elasticsearch")
        if not config.index:
            raise ValueError("index is required for Elasticsearch")

        hosts = [config.host]
        if "://" not in config.host:
            hosts = [f"http://{config.host}:{config.port or 9200}"]

        return await from_elasticsearch(
            hosts=hosts,
            index=config.index,
        )


class KafkaSourceCreator(DataSourceCreator):
    """Creator for Kafka data sources (async)."""

    def can_create(self, config: SourceConfig) -> bool:
        return config.source_type.lower() == SourceType.KAFKA

    def create(self, config: SourceConfig) -> Any:
        raise ValueError(
            "Kafka requires async creation. Use create_async() instead."
        )

    async def create_async(self, config: SourceConfig) -> Any:
        from truthound.datasources import from_kafka

        if not config.bootstrap_servers:
            raise ValueError("bootstrap_servers is required for Kafka")
        if not config.topic:
            raise ValueError("topic is required for Kafka")

        kwargs: dict[str, Any] = {
            "bootstrap_servers": config.bootstrap_servers,
            "topic": config.topic,
        }

        if config.group_id:
            kwargs["group_id"] = config.group_id
        if config.max_messages:
            kwargs["max_messages"] = config.max_messages

        return await from_kafka(**kwargs)


# =============================================================================
# Main Factory
# =============================================================================


class DataSourceFactory:
    """Factory for creating truthound DataSource objects.

    This factory uses the Strategy pattern to delegate creation
    to specialized creator classes. This design provides:
    - Extensibility: Add new creators without modifying factory
    - Testability: Easy to mock individual creators
    - Loose coupling: Truthound imports are isolated in creators

    Example:
        factory = DataSourceFactory()

        # From file
        source = factory.create(SourceConfig(source_type="csv", path="data.csv"))

        # From PostgreSQL
        source = factory.create(SourceConfig(
            source_type="postgresql",
            table="users",
            host="localhost",
            database="mydb",
        ))

        # From existing DB model config
        source = factory.create_from_dict(db_source.config)
    """

    def __init__(self) -> None:
        """Initialize factory with default creators."""
        self._creators: list[DataSourceCreator] = [
            FileSourceCreator(),
            SQLiteSourceCreator(),
            DuckDBSourceCreator(),
            PostgreSQLSourceCreator(),
            MySQLSourceCreator(),
            BigQuerySourceCreator(),
            SnowflakeSourceCreator(),
            RedshiftSourceCreator(),
            DatabricksSourceCreator(),
            OracleSourceCreator(),
            SQLServerSourceCreator(),
            MongoDBSourceCreator(),
            ElasticsearchSourceCreator(),
            KafkaSourceCreator(),
        ]

    def register_creator(self, creator: DataSourceCreator) -> None:
        """Register a custom data source creator.

        Args:
            creator: DataSourceCreator instance.
        """
        self._creators.insert(0, creator)

    def create(self, config: SourceConfig) -> Any:
        """Create a DataSource from configuration.

        Args:
            config: Source configuration.

        Returns:
            Truthound DataSource instance.

        Raises:
            ValueError: If source type is not supported or config is invalid.
            ImportError: If required driver is not installed.
        """
        source_type = config.source_type.lower()

        # Check for async sources
        if SourceType.is_async_type(source_type):
            raise ValueError(
                f"Async source type '{source_type}' requires async creation. "
                "Use create_async() instead."
            )

        # Find appropriate creator
        for creator in self._creators:
            if creator.can_create(config):
                return creator.create(config)

        raise ValueError(f"Unsupported source type: {source_type}")

    def create_from_dict(self, data: dict[str, Any]) -> Any:
        """Create a DataSource from a dictionary configuration.

        Args:
            data: Dictionary with source configuration.

        Returns:
            Truthound DataSource instance.
        """
        config = SourceConfig.from_dict(data)
        return self.create(config)

    async def create_async(self, config: SourceConfig) -> Any:
        """Create an async DataSource from configuration.

        Use this method for NoSQL and streaming sources that
        require async initialization.

        Args:
            config: Source configuration.

        Returns:
            Truthound async DataSource instance.

        Raises:
            ValueError: If source type doesn't support async.
        """
        source_type = config.source_type.lower()

        for creator in self._creators:
            if creator.can_create(config):
                if hasattr(creator, "create_async"):
                    return await creator.create_async(config)
                raise ValueError(
                    f"Source type '{source_type}' doesn't require async creation. "
                    "Use create() instead."
                )

        raise ValueError(f"Unsupported source type: {source_type}")


# =============================================================================
# Singleton and Convenience Functions
# =============================================================================


_factory: DataSourceFactory | None = None


def get_datasource_factory() -> DataSourceFactory:
    """Get singleton DataSourceFactory instance.

    Returns:
        DataSourceFactory singleton.
    """
    global _factory
    if _factory is None:
        _factory = DataSourceFactory()
    return _factory


def create_datasource(config: dict[str, Any] | SourceConfig) -> Any:
    """Convenience function to create a data source.

    Args:
        config: Source configuration (dict or SourceConfig).

    Returns:
        Truthound DataSource instance.
    """
    factory = get_datasource_factory()

    if isinstance(config, dict):
        return factory.create_from_dict(config)
    return factory.create(config)


async def create_datasource_async(config: dict[str, Any] | SourceConfig) -> Any:
    """Convenience function to create an async data source.

    Args:
        config: Source configuration (dict or SourceConfig).

    Returns:
        Truthound async DataSource instance.
    """
    factory = get_datasource_factory()

    if isinstance(config, dict):
        config = SourceConfig.from_dict(config)
    return await factory.create_async(config)


def get_source_path_or_datasource(
    source_type: str,
    config: dict[str, Any],
) -> str | Any:
    """Get either a file path or DataSource based on source type.

    This is a convenience function for backward compatibility.
    For file-based sources, returns the path string.
    For database sources, returns a DataSource object.

    Args:
        source_type: Source type string.
        config: Source configuration dict.

    Returns:
        File path string or DataSource object.
    """
    if SourceType.is_file_type(source_type):
        return config.get("path", "")

    # Create DataSource for non-file sources
    full_config = {"type": source_type, **config}
    return create_datasource(full_config)


# =============================================================================
# Utility Functions
# =============================================================================


def detect_file_type(path: str | Path) -> str | None:
    """Detect file type from path extension.

    Args:
        path: File path.

    Returns:
        File type string or None if unknown.
    """
    ext_map = {
        ".csv": "csv",
        ".parquet": "parquet",
        ".pq": "parquet",
        ".json": "json",
        ".ndjson": "ndjson",
        ".jsonl": "jsonl",
    }

    path = Path(path)
    ext = path.suffix.lower()
    return ext_map.get(ext)


def is_truthound_available() -> bool:
    """Check if truthound library is available.

    Returns:
        True if truthound can be imported.
    """
    try:
        import truthound
        return True
    except ImportError:
        return False


def get_truthound_version() -> str | None:
    """Get truthound library version if available.

    Returns:
        Version string or None.
    """
    try:
        import truthound
        return getattr(truthound, "__version__", None)
    except ImportError:
        return None


def get_datasource_auto(
    data: Any,
    *,
    table: str | None = None,
    query: str | None = None,
    **kwargs: Any,
) -> Any:
    """Auto-detect and create a DataSource using truthound's get_datasource.

    This function wraps truthound.datasources.get_datasource() for auto-detection
    of data source types. It's the recommended way to create DataSources when
    the type can be inferred from the input.

    Args:
        data: One of:
            - Polars DataFrame/LazyFrame
            - Pandas DataFrame
            - PySpark DataFrame
            - Dictionary (column -> values)
            - File path string (csv, parquet, json, etc.)
            - SQL connection string (postgresql://, mysql://, etc.)
        table: Table name for SQL sources.
        query: Custom SQL query for SQL sources.
        **kwargs: Additional arguments passed to the DataSource constructor.

    Returns:
        Appropriate DataSource for the input data type.

    Raises:
        ImportError: If truthound is not installed.
        ValueError: If data type cannot be detected.

    Example:
        # Auto-detect from Polars DataFrame
        ds = get_datasource_auto(pl_df)

        # Auto-detect from file path
        ds = get_datasource_auto("data.parquet")

        # Auto-detect from connection string
        ds = get_datasource_auto(
            "postgresql://user:pass@localhost/db",
            table="users",
        )
    """
    try:
        from truthound.datasources import get_datasource
        return get_datasource(data, table=table, query=query, **kwargs)
    except ImportError:
        raise ImportError(
            "truthound is not installed. Install with: pip install truthound"
        )


# =============================================================================
# Connection Testing
# =============================================================================


async def test_connection(config: SourceConfig | dict[str, Any]) -> dict[str, Any]:
    """Test connection to a data source.

    This function attempts to connect to the data source and retrieve
    basic metadata to verify connectivity.

    Args:
        config: Source configuration (SourceConfig or dict).

    Returns:
        Dictionary with connection test results:
        - success: bool - Whether connection succeeded
        - message: str - Success or error message
        - metadata: dict | None - Source metadata if successful
            - name: str - Source name
            - row_count: int | None - Row count if available
            - columns: list[str] | None - Column names if available
            - capabilities: list[str] | None - Source capabilities

    Example:
        result = await test_connection({
            "type": "postgresql",
            "host": "localhost",
            "database": "mydb",
            "table": "users",
        })
        if result["success"]:
            print(f"Connected! Found {result['metadata']['row_count']} rows")
        else:
            print(f"Connection failed: {result['message']}")
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    if isinstance(config, dict):
        config = SourceConfig.from_dict(config)

    result = {
        "success": False,
        "message": "",
        "metadata": None,
    }

    try:
        factory = get_datasource_factory()

        # Create datasource (may be async for MongoDB, ES, Kafka)
        if SourceType.is_async_type(config.source_type):
            datasource = await factory.create_async(config)
        else:
            # Run sync creation in thread pool to not block
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                datasource = await loop.run_in_executor(
                    executor, factory.create, config
                )

        # Extract metadata
        metadata: dict[str, Any] = {
            "name": getattr(datasource, "name", config.name or "unknown"),
        }

        # Try to get row count
        if hasattr(datasource, "row_count"):
            try:
                row_count = datasource.row_count
                metadata["row_count"] = row_count
            except Exception:
                metadata["row_count"] = None

        # Try to get columns
        if hasattr(datasource, "columns"):
            try:
                columns = datasource.columns
                metadata["columns"] = columns
            except Exception:
                metadata["columns"] = None

        # Try to get capabilities
        if hasattr(datasource, "capabilities"):
            try:
                capabilities = datasource.capabilities
                metadata["capabilities"] = [c.name for c in capabilities]
            except Exception:
                metadata["capabilities"] = None

        result["success"] = True
        result["message"] = "Connection successful"
        result["metadata"] = metadata

    except FileNotFoundError as e:
        result["message"] = f"File not found: {e}"
    except ImportError as e:
        result["message"] = f"Missing dependency: {e}"
    except ValueError as e:
        result["message"] = f"Configuration error: {e}"
    except Exception as e:
        result["message"] = f"Connection failed: {type(e).__name__}: {e}"

    return result


def get_source_capabilities(
    source_type: str,
) -> set[str]:
    """Get the capabilities supported by a source type.

    Args:
        source_type: Source type string (e.g., "postgresql", "csv").

    Returns:
        Set of capability names supported by the source type.
    """
    from truthound_dashboard.core.interfaces import DataSourceCapability

    # Map source types to their capabilities
    capability_map: dict[str, set[DataSourceCapability]] = {
        # File sources
        "file": {DataSourceCapability.SCHEMA_INFERENCE, DataSourceCapability.LAZY_EVALUATION},
        "csv": {DataSourceCapability.SCHEMA_INFERENCE, DataSourceCapability.LAZY_EVALUATION},
        "parquet": {DataSourceCapability.SCHEMA_INFERENCE, DataSourceCapability.LAZY_EVALUATION, DataSourceCapability.ROW_COUNT},
        "json": {DataSourceCapability.SCHEMA_INFERENCE, DataSourceCapability.LAZY_EVALUATION},
        "ndjson": {DataSourceCapability.SCHEMA_INFERENCE, DataSourceCapability.LAZY_EVALUATION, DataSourceCapability.STREAMING},
        "jsonl": {DataSourceCapability.SCHEMA_INFERENCE, DataSourceCapability.LAZY_EVALUATION, DataSourceCapability.STREAMING},
        # SQL sources
        "sqlite": {DataSourceCapability.SQL_PUSHDOWN, DataSourceCapability.ROW_COUNT, DataSourceCapability.SAMPLING, DataSourceCapability.CONNECTION_TEST},
        "postgresql": {DataSourceCapability.SQL_PUSHDOWN, DataSourceCapability.ROW_COUNT, DataSourceCapability.SAMPLING, DataSourceCapability.CONNECTION_TEST},
        "mysql": {DataSourceCapability.SQL_PUSHDOWN, DataSourceCapability.ROW_COUNT, DataSourceCapability.SAMPLING, DataSourceCapability.CONNECTION_TEST},
        "duckdb": {DataSourceCapability.SQL_PUSHDOWN, DataSourceCapability.ROW_COUNT, DataSourceCapability.SAMPLING, DataSourceCapability.LAZY_EVALUATION},
        # Cloud DW
        "bigquery": {DataSourceCapability.SQL_PUSHDOWN, DataSourceCapability.ROW_COUNT, DataSourceCapability.SAMPLING, DataSourceCapability.CONNECTION_TEST},
        "snowflake": {DataSourceCapability.SQL_PUSHDOWN, DataSourceCapability.ROW_COUNT, DataSourceCapability.SAMPLING, DataSourceCapability.CONNECTION_TEST},
        "redshift": {DataSourceCapability.SQL_PUSHDOWN, DataSourceCapability.ROW_COUNT, DataSourceCapability.SAMPLING, DataSourceCapability.CONNECTION_TEST},
        "databricks": {DataSourceCapability.SQL_PUSHDOWN, DataSourceCapability.ROW_COUNT, DataSourceCapability.SAMPLING, DataSourceCapability.CONNECTION_TEST},
        # Enterprise
        "oracle": {DataSourceCapability.SQL_PUSHDOWN, DataSourceCapability.ROW_COUNT, DataSourceCapability.SAMPLING, DataSourceCapability.CONNECTION_TEST},
        "sqlserver": {DataSourceCapability.SQL_PUSHDOWN, DataSourceCapability.ROW_COUNT, DataSourceCapability.SAMPLING, DataSourceCapability.CONNECTION_TEST},
        # NoSQL
        "mongodb": {DataSourceCapability.SAMPLING, DataSourceCapability.CONNECTION_TEST},
        "elasticsearch": {DataSourceCapability.SAMPLING, DataSourceCapability.CONNECTION_TEST},
        # Streaming
        "kafka": {DataSourceCapability.STREAMING, DataSourceCapability.CONNECTION_TEST},
        # DataFrame
        "polars": {DataSourceCapability.LAZY_EVALUATION, DataSourceCapability.ROW_COUNT, DataSourceCapability.SCHEMA_INFERENCE},
        "pandas": {DataSourceCapability.ROW_COUNT, DataSourceCapability.SCHEMA_INFERENCE},
    }

    source_type_lower = source_type.lower()
    capabilities = capability_map.get(source_type_lower, set())
    return {c.name for c in capabilities}
