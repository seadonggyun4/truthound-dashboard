"""Validators API endpoints.

This module provides API endpoints for validator discovery and configuration.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from ..schemas.validators import (
    VALIDATOR_REGISTRY,
    ValidatorCategory,
    ValidatorDefinition,
    get_validator_by_name,
    get_validators_by_category,
    search_validators,
)

router = APIRouter()


@router.get(
    "/validators",
    response_model=list[ValidatorDefinition],
    summary="List all validators",
    description="Returns all available validators with their parameter definitions.",
)
async def list_validators(
    category: ValidatorCategory | None = Query(
        default=None, description="Filter by category"
    ),
    search: str | None = Query(
        default=None, description="Search by name, description, or tags"
    ),
) -> list[ValidatorDefinition]:
    """List all validators, optionally filtered.

    Args:
        category: Optional category filter.
        search: Optional search query.

    Returns:
        List of validator definitions.
    """
    if search:
        return search_validators(search)
    if category:
        return get_validators_by_category(category)
    return VALIDATOR_REGISTRY


@router.get(
    "/validators/categories",
    response_model=list[dict[str, str]],
    summary="List validator categories",
    description="Returns all validator categories with their labels.",
)
async def list_categories() -> list[dict[str, str]]:
    """List all validator categories.

    Returns:
        List of category objects with value and label.
    """
    return [
        {"value": c.value, "label": c.value.replace("_", " ").title()}
        for c in ValidatorCategory
    ]


@router.get(
    "/validators/{name}",
    response_model=ValidatorDefinition | None,
    summary="Get validator by name",
    description="Returns a single validator definition by its name.",
)
async def get_validator(name: str) -> ValidatorDefinition | None:
    """Get a validator by name.

    Args:
        name: Validator name.

    Returns:
        Validator definition if found.
    """
    return get_validator_by_name(name)
