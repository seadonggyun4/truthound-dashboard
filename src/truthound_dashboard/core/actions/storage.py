"""Storage action implementations.

Provides actions for storing validation results to various backends:
- Local filesystem
- Amazon S3
- Google Cloud Storage

These actions persist validation results for historical analysis,
compliance, and audit purposes.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from truthound_dashboard.core.interfaces.actions import (
    ActionConfig,
    ActionContext,
    ActionResult,
    ActionStatus,
    BaseAction,
    NotifyCondition,
    register_action,
)

logger = logging.getLogger(__name__)


# =============================================================================
# File Storage Action
# =============================================================================


@dataclass
class FileStorageConfig(ActionConfig):
    """Configuration for file storage action.

    Attributes:
        base_path: Base directory for storage.
        file_format: Output format (json, csv, parquet).
        include_issues: Include detailed issues.
        create_dirs: Create directories if missing.
        filename_template: Template for filename.
        compress: Compress output files.
    """

    base_path: str = "./validation_results"
    file_format: str = "json"
    include_issues: bool = True
    create_dirs: bool = True
    filename_template: str = "{checkpoint_name}_{run_id}.{format}"
    compress: bool = False

    def __post_init__(self):
        self.name = self.name or "file_storage"
        self.notify_on = NotifyCondition.ALWAYS


@register_action("file_storage")
class FileStorageAction(BaseAction):
    """Store validation results to local filesystem.

    Saves results as JSON, CSV, or Parquet files for historical tracking.

    Example:
        action = FileStorageAction(
            base_path="/data/validations",
            file_format="json",
        )
    """

    def __init__(
        self,
        base_path: str = "./validation_results",
        file_format: str = "json",
        config: FileStorageConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = FileStorageConfig(
                base_path=base_path,
                file_format=file_format,
                **kwargs,
            )
        elif isinstance(config, dict):
            config = FileStorageConfig(**config)

        super().__init__(config)
        self._storage_config: FileStorageConfig = config

    @property
    def action_type(self) -> str:
        return "storage"

    def _do_execute(self, context: ActionContext) -> ActionResult:
        """Store result to file."""
        result = context.checkpoint_result

        # Build file path
        filename = self._storage_config.filename_template.format(
            checkpoint_name=result.checkpoint_name.replace(" ", "_"),
            run_id=result.run_id,
            format=self._storage_config.file_format,
            date=datetime.now().strftime("%Y%m%d"),
            timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"),
        )

        base_path = Path(self._storage_config.base_path)
        if self._storage_config.create_dirs:
            base_path.mkdir(parents=True, exist_ok=True)

        file_path = base_path / filename

        try:
            # Build data to store
            data = result.to_dict()
            if not self._storage_config.include_issues:
                data.pop("issues", None)

            # Write based on format
            if self._storage_config.file_format == "json":
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
            elif self._storage_config.file_format == "csv":
                self._write_csv(file_path, data)
            elif self._storage_config.file_format == "parquet":
                self._write_parquet(file_path, data)
            else:
                raise ValueError(f"Unsupported format: {self._storage_config.file_format}")

            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.SUCCESS,
                message=f"Result stored to {file_path}",
                details={"file_path": str(file_path), "format": self._storage_config.file_format},
            )
        except Exception as e:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message=f"Failed to store result: {str(e)}",
                error=str(e),
            )

    def _write_csv(self, path: Path, data: dict[str, Any]) -> None:
        """Write data as CSV."""
        import csv

        # Flatten issues for CSV
        rows = []
        for issue in data.get("issues", []):
            row = {
                "run_id": data["run_id"],
                "checkpoint_name": data["checkpoint_name"],
                "source_name": data["source_name"],
                "status": data["status"],
                "column": issue.get("column", ""),
                "issue_type": issue.get("issue_type", ""),
                "count": issue.get("count", 0),
                "severity": issue.get("severity", ""),
            }
            rows.append(row)

        if rows:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        else:
            # Write summary if no issues
            summary_row = {
                "run_id": data["run_id"],
                "checkpoint_name": data["checkpoint_name"],
                "source_name": data["source_name"],
                "status": data["status"],
                "row_count": data["row_count"],
                "issue_count": data["issue_count"],
            }
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=summary_row.keys())
                writer.writeheader()
                writer.writerow(summary_row)

    def _write_parquet(self, path: Path, data: dict[str, Any]) -> None:
        """Write data as Parquet using Polars."""
        import polars as pl

        # Convert to DataFrame
        issues = data.get("issues", [])
        if issues:
            df = pl.DataFrame(issues)
            df = df.with_columns([
                pl.lit(data["run_id"]).alias("run_id"),
                pl.lit(data["checkpoint_name"]).alias("checkpoint_name"),
                pl.lit(data["source_name"]).alias("source_name"),
            ])
        else:
            df = pl.DataFrame({
                "run_id": [data["run_id"]],
                "checkpoint_name": [data["checkpoint_name"]],
                "source_name": [data["source_name"]],
                "status": [data["status"]],
                "row_count": [data["row_count"]],
                "issue_count": [data["issue_count"]],
            })

        df.write_parquet(path)


# =============================================================================
# S3 Storage Action
# =============================================================================


@dataclass
class S3StorageConfig(ActionConfig):
    """Configuration for S3 storage action.

    Attributes:
        bucket: S3 bucket name.
        prefix: Key prefix for objects.
        region: AWS region.
        access_key_id: AWS access key (optional, uses env/IAM if not set).
        secret_access_key: AWS secret key.
        file_format: Output format.
        include_issues: Include detailed issues.
    """

    bucket: str = ""
    prefix: str = "validations"
    region: str = "us-east-1"
    access_key_id: str | None = None
    secret_access_key: str | None = None
    file_format: str = "json"
    include_issues: bool = True

    def __post_init__(self):
        self.name = self.name or "s3_storage"
        self.notify_on = NotifyCondition.ALWAYS


@register_action("s3_storage")
class S3StorageAction(BaseAction):
    """Store validation results to Amazon S3.

    Uploads results to an S3 bucket for durable storage.
    Uses boto3 for S3 operations.

    Example:
        action = S3StorageAction(
            bucket="my-validations",
            prefix="data-quality/daily",
        )
    """

    def __init__(
        self,
        bucket: str = "",
        prefix: str = "validations",
        config: S3StorageConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = S3StorageConfig(
                bucket=bucket,
                prefix=prefix,
                **kwargs,
            )
        elif isinstance(config, dict):
            config = S3StorageConfig(**config)

        super().__init__(config)
        self._s3_config: S3StorageConfig = config

    @property
    def action_type(self) -> str:
        return "storage"

    def _do_execute(self, context: ActionContext) -> ActionResult:
        """Store result to S3."""
        try:
            import boto3
        except ImportError:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message="boto3 not installed. Install with: pip install boto3",
                error="ImportError: boto3",
            )

        result = context.checkpoint_result

        # Build S3 key
        timestamp = datetime.now().strftime("%Y/%m/%d")
        filename = f"{result.checkpoint_name}_{result.run_id}.{self._s3_config.file_format}"
        key = f"{self._s3_config.prefix}/{timestamp}/{filename}"

        try:
            # Create S3 client
            client_kwargs = {"region_name": self._s3_config.region}
            if self._s3_config.access_key_id:
                client_kwargs["aws_access_key_id"] = self._s3_config.access_key_id
                client_kwargs["aws_secret_access_key"] = self._s3_config.secret_access_key

            s3 = boto3.client("s3", **client_kwargs)

            # Build data
            data = result.to_dict()
            if not self._s3_config.include_issues:
                data.pop("issues", None)

            # Serialize
            body = json.dumps(data, indent=2, default=str)

            # Upload
            s3.put_object(
                Bucket=self._s3_config.bucket,
                Key=key,
                Body=body.encode("utf-8"),
                ContentType="application/json",
            )

            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.SUCCESS,
                message=f"Result stored to s3://{self._s3_config.bucket}/{key}",
                details={"bucket": self._s3_config.bucket, "key": key},
            )
        except Exception as e:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message=f"Failed to store to S3: {str(e)}",
                error=str(e),
            )


# =============================================================================
# GCS Storage Action
# =============================================================================


@dataclass
class GCSStorageConfig(ActionConfig):
    """Configuration for Google Cloud Storage action.

    Attributes:
        bucket: GCS bucket name.
        prefix: Object prefix.
        project: GCP project ID.
        credentials_path: Path to service account JSON.
        file_format: Output format.
        include_issues: Include detailed issues.
    """

    bucket: str = ""
    prefix: str = "validations"
    project: str | None = None
    credentials_path: str | None = None
    file_format: str = "json"
    include_issues: bool = True

    def __post_init__(self):
        self.name = self.name or "gcs_storage"
        self.notify_on = NotifyCondition.ALWAYS


@register_action("gcs_storage")
class GCSStorageAction(BaseAction):
    """Store validation results to Google Cloud Storage.

    Uploads results to a GCS bucket for durable storage.
    Uses google-cloud-storage for GCS operations.

    Example:
        action = GCSStorageAction(
            bucket="my-validations",
            prefix="data-quality/daily",
        )
    """

    def __init__(
        self,
        bucket: str = "",
        prefix: str = "validations",
        config: GCSStorageConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = GCSStorageConfig(
                bucket=bucket,
                prefix=prefix,
                **kwargs,
            )
        elif isinstance(config, dict):
            config = GCSStorageConfig(**config)

        super().__init__(config)
        self._gcs_config: GCSStorageConfig = config

    @property
    def action_type(self) -> str:
        return "storage"

    def _do_execute(self, context: ActionContext) -> ActionResult:
        """Store result to GCS."""
        try:
            from google.cloud import storage
        except ImportError:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message="google-cloud-storage not installed. Install with: pip install google-cloud-storage",
                error="ImportError: google-cloud-storage",
            )

        result = context.checkpoint_result

        # Build GCS path
        timestamp = datetime.now().strftime("%Y/%m/%d")
        filename = f"{result.checkpoint_name}_{result.run_id}.{self._gcs_config.file_format}"
        blob_name = f"{self._gcs_config.prefix}/{timestamp}/{filename}"

        try:
            # Create GCS client
            if self._gcs_config.credentials_path:
                client = storage.Client.from_service_account_json(
                    self._gcs_config.credentials_path
                )
            else:
                client = storage.Client(project=self._gcs_config.project)

            bucket = client.bucket(self._gcs_config.bucket)
            blob = bucket.blob(blob_name)

            # Build data
            data = result.to_dict()
            if not self._gcs_config.include_issues:
                data.pop("issues", None)

            # Upload
            blob.upload_from_string(
                json.dumps(data, indent=2, default=str),
                content_type="application/json",
            )

            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.SUCCESS,
                message=f"Result stored to gs://{self._gcs_config.bucket}/{blob_name}",
                details={"bucket": self._gcs_config.bucket, "blob": blob_name},
            )
        except Exception as e:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message=f"Failed to store to GCS: {str(e)}",
                error=str(e),
            )
