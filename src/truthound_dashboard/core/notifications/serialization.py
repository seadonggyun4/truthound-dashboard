"""Serialization helpers for notification channel configs.

These helpers keep notification channel read paths secret-safe while still
allowing the runtime to materialize credentials immediately before use.
"""

from __future__ import annotations

import json
from typing import Any

from ..encryption import is_sensitive_field, mask_sensitive_value

from ..secrets import (
    SECRET_HINT_KEY,
    SECRET_REDACTED_KEY,
    get_secret_hint,
    is_redacted_secret_payload,
    is_secret_ref_payload,
)
from .base import ChannelRegistry


def get_channel_schema(channel_type: str) -> dict[str, Any]:
    channel_class = ChannelRegistry.get(channel_type)
    if channel_class is None:
        return {}
    return channel_class.get_config_schema()


def get_channel_secret_fields(channel_type: str) -> set[str]:
    schema = get_channel_schema(channel_type)
    fields: set[str] = set()
    for field_name, field_schema in schema.items():
        if field_schema.get("secret") is True or is_sensitive_field(field_name):
            fields.add(field_name)
    return fields


def _split_lines(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]
    return []


def _split_csv(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _parse_json_object(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str) and value.strip():
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
        raise ValueError("Expected a JSON object")
    return {}


def normalize_channel_config(channel_type: str, config: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(config or {})

    if channel_type == "email":
        if "from_email" in normalized and "from_address" not in normalized:
            normalized["from_address"] = normalized.pop("from_email")
        if "recipients" in normalized and "to_addresses" not in normalized:
            normalized["to_addresses"] = _split_lines(normalized.pop("recipients"))
        if "to_addresses" in normalized:
            normalized["to_addresses"] = _split_lines(normalized["to_addresses"])
        if "cc_addresses" in normalized:
            normalized["cc_addresses"] = _split_lines(normalized["cc_addresses"])

    elif channel_type == "webhook":
        if "include_event_data" in normalized and "include_result" not in normalized:
            normalized["include_result"] = normalized.pop("include_event_data")
        if "headers" in normalized:
            normalized["headers"] = _parse_json_object(normalized["headers"])

    elif channel_type == "opsgenie":
        if "tags" in normalized:
            normalized["tags"] = _split_csv(normalized["tags"])

    elif channel_type == "github":
        if "labels" in normalized:
            normalized["labels"] = _split_csv(normalized["labels"])
        if "assignees" in normalized:
            normalized["assignees"] = _split_csv(normalized["assignees"])

    return normalized


def redact_channel_config(channel_type: str, config: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    secret_fields = get_channel_secret_fields(channel_type)

    for key, value in (config or {}).items():
        if is_secret_ref_payload(value):
            redacted[key] = value
        elif key in secret_fields and isinstance(value, str) and value:
            redacted[key] = {
                SECRET_REDACTED_KEY: True,
                SECRET_HINT_KEY: mask_sensitive_value(value),
            }
        elif key in secret_fields and is_redacted_secret_payload(value):
            redacted[key] = value
        elif isinstance(value, dict):
            redacted[key] = redact_channel_config(channel_type, value)
        else:
            redacted[key] = value

    return redacted


def channel_has_stored_secrets(channel_type: str, config: dict[str, Any]) -> bool:
    secret_fields = get_channel_secret_fields(channel_type)
    for key, value in (config or {}).items():
        if key in secret_fields and (
            is_secret_ref_payload(value)
            or is_redacted_secret_payload(value)
            or (isinstance(value, str) and bool(value))
        ):
            return True
        if isinstance(value, dict) and channel_has_stored_secrets(channel_type, value):
            return True
    return False


def channel_config_summary(channel_type: str, config: dict[str, Any]) -> str:
    config = config or {}

    if channel_type in {"slack", "discord", "teams"}:
        webhook = config.get("webhook_url")
        if webhook:
            return f"Webhook: {get_secret_hint(webhook)}"

    if channel_type == "email":
        recipients = config.get("recipients") or config.get("to_addresses")
        if isinstance(recipients, list):
            preview = ", ".join(str(item) for item in recipients[:2])
            suffix = "..." if len(recipients) > 2 else ""
            return f"Recipients: {preview}{suffix}" if preview else "Recipients configured"
        if isinstance(recipients, str):
            lines = [line.strip() for line in recipients.splitlines() if line.strip()]
            preview = ", ".join(lines[:2])
            suffix = "..." if len(lines) > 2 else ""
            return f"Recipients: {preview}{suffix}" if preview else "Recipients configured"
        return "Email channel configured"

    if channel_type == "webhook" and isinstance(config.get("url"), str):
        url = str(config["url"])
        return f"URL: {url[:50]}..." if len(url) > 50 else f"URL: {url}"

    for key, value in config.items():
        if key in get_channel_secret_fields(channel_type):
            continue
        if isinstance(value, (str, int, float, bool)) and value not in ("", None):
            return f"{key.replace('_', ' ').title()}: {value}"

    if channel_has_stored_secrets(channel_type, config):
        return "Stored credentials"
    return "Configured"
