"""Rule suggestion API endpoints.

This module provides endpoints for generating and applying
validation rule suggestions based on profile data.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from truthound_dashboard.schemas import (
    ApplyRulesRequest,
    ApplyRulesResponse,
    RuleSuggestionRequest,
    RuleSuggestionResponse,
)

from .deps import (
    ProfileServiceDep,
    RuleGeneratorServiceDep,
    SchemaServiceDep,
    SourceServiceDep,
)

router = APIRouter(prefix="/sources", tags=["rule-suggestions"])


@router.post(
    "/{source_id}/rules/suggest",
    response_model=RuleSuggestionResponse,
    summary="Generate rule suggestions",
    description="Generate validation rule suggestions based on profile data.",
)
async def suggest_rules(
    source_id: str,
    generator_service: RuleGeneratorServiceDep,
    profile_service: ProfileServiceDep,
    schema_service: SchemaServiceDep,
    source_service: SourceServiceDep,
    request: RuleSuggestionRequest | None = None,
) -> RuleSuggestionResponse:
    """Generate rule suggestions for a source.

    Args:
        source_id: Source ID.
        generator_service: Rule generator service.
        profile_service: Profile service.
        schema_service: Schema service.
        source_service: Source service.
        request: Optional request parameters.

    Returns:
        Rule suggestion response.
    """
    # Verify source exists
    source = await source_service.get(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found",
        )

    # Parse request
    if request is None:
        request = RuleSuggestionRequest()

    # Get profile
    if request.profile_id and not request.use_latest_profile:
        profile = await profile_service.get(request.profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile {request.profile_id} not found",
            )
    else:
        profile = await profile_service.get_latest(source_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No profile found for source {source_id}. Run profiling first.",
            )

    # Get schema (optional)
    schema = await schema_service.get_active(source_id)

    # Generate suggestions
    result = await generator_service.generate_suggestions(
        source,
        profile,
        schema,
        min_confidence=request.min_confidence,
    )

    return result


@router.post(
    "/{source_id}/rules/apply-suggestions",
    response_model=ApplyRulesResponse,
    summary="Apply rule suggestions",
    description="Apply selected rule suggestions to create validation rules.",
)
async def apply_rule_suggestions(
    source_id: str,
    request: ApplyRulesRequest,
    generator_service: RuleGeneratorServiceDep,
    source_service: SourceServiceDep,
) -> ApplyRulesResponse:
    """Apply selected rule suggestions.

    Args:
        source_id: Source ID.
        request: Apply rules request.
        generator_service: Rule generator service.
        source_service: Source service.

    Returns:
        Apply rules response.
    """
    # Verify source exists
    source = await source_service.get(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found",
        )

    # Validate request
    if not request.suggestions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No suggestions provided to apply",
        )

    # Apply suggestions
    result = await generator_service.apply_suggestions(
        source,
        request.suggestions,
        rule_name=request.rule_name,
        rule_description=request.rule_description,
    )

    return result
