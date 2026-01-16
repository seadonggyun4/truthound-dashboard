"""Rule suggestion Pydantic schemas.

This module defines schemas for automatic rule generation
from profile data, including suggestions and application.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from .base import BaseSchema


# =============================================================================
# Suggested Rule Schemas
# =============================================================================


class SuggestedRule(BaseSchema):
    """A single suggested validation rule."""

    column: str = Field(..., description="Target column name")
    validator_name: str = Field(..., description="Validator to apply")
    params: dict[str, Any] = Field(
        default_factory=dict, description="Validator parameters"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0)",
    )
    reason: str = Field(..., description="Why this rule is suggested")
    severity_suggestion: str = Field(
        default="medium",
        description="Suggested severity level",
    )


class RuleSuggestionRequest(BaseSchema):
    """Request to generate rule suggestions."""

    use_latest_profile: bool = Field(
        default=True,
        description="Use the latest profile for suggestions",
    )
    profile_id: str | None = Field(
        default=None,
        description="Specific profile ID to use (if not latest)",
    )
    min_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for suggestions",
    )
    include_types: list[str] | None = Field(
        default=None,
        description="Only suggest rules for these validator types",
    )
    exclude_columns: list[str] | None = Field(
        default=None,
        description="Columns to exclude from suggestions",
    )


class RuleSuggestionResponse(BaseSchema):
    """Response containing suggested rules."""

    source_id: str = Field(..., description="Source ID")
    source_name: str = Field(..., description="Source name")
    profile_id: str = Field(..., description="Profile ID used for suggestions")
    suggestions: list[SuggestedRule] = Field(
        default_factory=list, description="List of suggested rules"
    )
    total_suggestions: int = Field(default=0, description="Total suggestions count")
    high_confidence_count: int = Field(
        default=0, description="Suggestions with confidence >= 0.8"
    )
    generated_at: datetime = Field(..., description="When suggestions were generated")


# =============================================================================
# Apply Rules Schemas
# =============================================================================


class ApplyRulesRequest(BaseSchema):
    """Request to apply selected rule suggestions."""

    suggestions: list[SuggestedRule] = Field(
        ..., description="Selected suggestions to apply"
    )
    create_new_rule: bool = Field(
        default=True,
        description="Create a new rule set (vs updating existing)",
    )
    rule_name: str | None = Field(
        default=None,
        description="Name for the new rule set",
    )
    rule_description: str | None = Field(
        default=None,
        description="Description for the new rule set",
    )


class ApplyRulesResponse(BaseSchema):
    """Response after applying rule suggestions."""

    source_id: str = Field(..., description="Source ID")
    rule_id: str = Field(..., description="Created/updated rule ID")
    rule_name: str = Field(..., description="Rule name")
    applied_count: int = Field(..., description="Number of rules applied")
    validators: list[str] = Field(
        default_factory=list, description="Applied validator names"
    )
    created_at: datetime = Field(..., description="When rule was created/updated")


# =============================================================================
# Suggestion Statistics
# =============================================================================


class SuggestionStats(BaseSchema):
    """Statistics about rule suggestions for a source."""

    source_id: str = Field(..., description="Source ID")
    last_suggestion_at: datetime | None = Field(
        default=None, description="Last suggestion generation time"
    )
    total_suggestions_generated: int = Field(
        default=0, description="Total suggestions ever generated"
    )
    total_suggestions_applied: int = Field(
        default=0, description="Total suggestions applied"
    )
    suggestion_types: dict[str, int] = Field(
        default_factory=dict,
        description="Count of suggestions by validator type",
    )
