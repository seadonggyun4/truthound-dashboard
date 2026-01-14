"""Validator registry module.

This module provides a modular, extensible validator registry system.
Each validator category is defined in a separate module for maintainability.

Usage:
    from truthound_dashboard.schemas.validators import (
        VALIDATOR_REGISTRY,
        get_validator_by_name,
        get_validators_by_category,
        search_validators,
        ValidatorDefinition,
        ValidatorConfig,
        ValidatorCategory,
    )
"""

from __future__ import annotations

from .base import (
    ParameterDefinition,
    ParameterType,
    ValidatorCategory,
    ValidatorConfig,
    ValidatorConfigList,
    ValidatorDefinition,
    configs_to_truthound_format,
    has_custom_params,
    merge_severity_overrides,
)
from .registry import (
    VALIDATOR_REGISTRY,
    get_validator_by_name,
    get_validators_by_category,
    search_validators,
    get_category_info,
    CATEGORY_INFO,
)

__all__ = [
    # Base types
    "ParameterDefinition",
    "ParameterType",
    "ValidatorCategory",
    "ValidatorConfig",
    "ValidatorConfigList",
    "ValidatorDefinition",
    # Utility functions
    "configs_to_truthound_format",
    "has_custom_params",
    "merge_severity_overrides",
    # Registry
    "VALIDATOR_REGISTRY",
    "get_validator_by_name",
    "get_validators_by_category",
    "search_validators",
    "get_category_info",
    "CATEGORY_INFO",
]
