"""Built-in validator registry API."""

from __future__ import annotations

from fastapi import APIRouter, Query

from ..schemas.validators import (
    VALIDATOR_REGISTRY,
    UnifiedValidatorDefinition,
    UnifiedValidatorListResponse,
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
    summary="List built-in validators",
    description="Returns all built-in validators with their parameter definitions.",
)
async def list_validators(
    category: ValidatorCategory | None = Query(default=None, description="Filter by category"),
    search: str | None = Query(default=None, description="Search by name, description, or tags"),
) -> list[ValidatorDefinition]:
    if search:
        return search_validators(search)
    if category:
        return get_validators_by_category(category)
    return VALIDATOR_REGISTRY


@router.get(
    "/validators/unified",
    response_model=UnifiedValidatorListResponse,
    summary="List built-in validators in unified shape",
    description="Returns built-in validators using the unified dashboard response shape.",
)
async def list_unified_validators(
    category: str | None = Query(default=None, description="Filter by category"),
    search: str | None = Query(default=None, description="Search by name, description, or tags"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> UnifiedValidatorListResponse:
    validators = VALIDATOR_REGISTRY
    if search:
        search_lower = search.lower()
        validators = [
            validator for validator in validators
            if (
                search_lower in validator.name.lower()
                or search_lower in validator.display_name.lower()
                or search_lower in validator.description.lower()
                or any(search_lower in tag.lower() for tag in validator.tags)
            )
        ]
    if category:
        validators = [validator for validator in validators if validator.category.value == category]

    unified_validators = [
        UnifiedValidatorDefinition.from_builtin(validator) for validator in validators
    ]
    category_counts: dict[str, int] = {}
    for validator in unified_validators:
        category_counts[validator.category] = category_counts.get(validator.category, 0) + 1

    categories = [
        {
            "name": name,
            "label": name.replace("_", " ").title(),
            "builtin_count": count,
            "custom_count": 0,
            "total": count,
        }
        for name, count in sorted(category_counts.items())
    ]

    total = len(unified_validators)
    return UnifiedValidatorListResponse(
        data=unified_validators[offset : offset + limit],
        total=total,
        builtin_count=total,
        custom_count=0,
        categories=categories,
    )


@router.get(
    "/validators/categories",
    response_model=list[dict[str, str]],
    summary="List validator categories",
    description="Returns all validator categories with their labels.",
)
async def list_categories() -> list[dict[str, str]]:
    return [
        {"value": category.value, "label": category.value.replace("_", " ").title()}
        for category in ValidatorCategory
    ]


@router.get(
    "/validators/{name}",
    response_model=ValidatorDefinition | None,
    summary="Get validator by name",
    description="Returns a single validator definition by its name.",
)
async def get_validator(name: str) -> ValidatorDefinition | None:
    return get_validator_by_name(name)
