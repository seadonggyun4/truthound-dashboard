"""Rule generation service.

This module provides functionality for automatically generating
validation rules based on profile data analysis.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db import Profile, Rule, Schema, Source
from truthound_dashboard.core.services import ProfileRepository, RuleRepository
from truthound_dashboard.schemas.rule_suggestion import (
    ApplyRulesResponse,
    RuleSuggestionResponse,
    SuggestedRule,
)


# Common email pattern
EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

# Common date patterns
DATE_PATTERNS = [
    r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
    r"\d{2}/\d{2}/\d{4}",  # MM/DD/YYYY
    r"\d{2}-\d{2}-\d{4}",  # DD-MM-YYYY
]


def _parse_percentage(value: str | None) -> float:
    """Parse percentage string to float.

    Args:
        value: Percentage string like "25.5%".

    Returns:
        Float value (0.0-100.0).
    """
    if not value:
        return 0.0
    try:
        return float(value.replace("%", ""))
    except (ValueError, AttributeError):
        return 0.0


class RuleGeneratorService:
    """Service for generating validation rules from profile data."""

    def __init__(self, session: AsyncSession):
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.profile_repo = ProfileRepository(session)
        self.rule_repo = RuleRepository(session)

    def _suggest_null_rules(
        self,
        column: dict[str, Any],
    ) -> list[SuggestedRule]:
        """Suggest null-related validators based on null percentage.

        Args:
            column: Column profile data.

        Returns:
            List of suggested rules.
        """
        suggestions = []
        col_name = column.get("name", "")
        null_pct = _parse_percentage(column.get("null_pct"))

        if null_pct == 0.0:
            # Column has no nulls - suggest NotNull
            suggestions.append(
                SuggestedRule(
                    column=col_name,
                    validator_name="NotNull",
                    params={},
                    confidence=0.95,
                    reason="Column has 0% null values",
                    severity_suggestion="high",
                )
            )
        elif null_pct < 1.0:
            # Very few nulls - suggest Null with mostly
            suggestions.append(
                SuggestedRule(
                    column=col_name,
                    validator_name="Null",
                    params={"mostly": 0.99},
                    confidence=0.85,
                    reason=f"Column has only {null_pct}% null values",
                    severity_suggestion="medium",
                )
            )
        elif null_pct < 5.0:
            # Some nulls - suggest Null with lower threshold
            suggestions.append(
                SuggestedRule(
                    column=col_name,
                    validator_name="Null",
                    params={"mostly": 0.95},
                    confidence=0.7,
                    reason=f"Column has {null_pct}% null values",
                    severity_suggestion="low",
                )
            )

        return suggestions

    def _suggest_uniqueness_rules(
        self,
        column: dict[str, Any],
    ) -> list[SuggestedRule]:
        """Suggest uniqueness validators based on unique percentage.

        Args:
            column: Column profile data.

        Returns:
            List of suggested rules.
        """
        suggestions = []
        col_name = column.get("name", "")
        unique_pct = _parse_percentage(column.get("unique_pct"))
        distinct_count = column.get("distinct_count")

        if unique_pct >= 99.9:
            # Nearly unique - suggest Unique
            suggestions.append(
                SuggestedRule(
                    column=col_name,
                    validator_name="Unique",
                    params={},
                    confidence=0.95,
                    reason=f"Column has {unique_pct}% unique values (likely primary key)",
                    severity_suggestion="high",
                )
            )
        elif unique_pct >= 95.0:
            # High uniqueness - suggest Unique with tolerance
            suggestions.append(
                SuggestedRule(
                    column=col_name,
                    validator_name="Unique",
                    params={"mostly": 0.95},
                    confidence=0.8,
                    reason=f"Column has {unique_pct}% unique values",
                    severity_suggestion="medium",
                )
            )
        elif unique_pct < 10.0 and distinct_count and distinct_count < 50:
            # Low cardinality - suggest DistinctSet
            suggestions.append(
                SuggestedRule(
                    column=col_name,
                    validator_name="DistinctSet",
                    params={"max_distinct": distinct_count + 10},
                    confidence=0.75,
                    reason=f"Column has low cardinality ({distinct_count} distinct values)",
                    severity_suggestion="low",
                )
            )

        return suggestions

    def _suggest_range_rules(
        self,
        column: dict[str, Any],
    ) -> list[SuggestedRule]:
        """Suggest range validators based on min/max values.

        Args:
            column: Column profile data.

        Returns:
            List of suggested rules.
        """
        suggestions = []
        col_name = column.get("name", "")
        dtype = column.get("dtype", "").lower()
        min_val = column.get("min")
        max_val = column.get("max")

        # Only suggest for numeric types
        if dtype not in ("int64", "int32", "float64", "float32", "number", "integer"):
            return suggestions

        if min_val is not None and max_val is not None:
            try:
                min_num = float(min_val)
                max_num = float(max_val)

                # Only suggest if range seems reasonable
                if max_num > min_num:
                    suggestions.append(
                        SuggestedRule(
                            column=col_name,
                            validator_name="Range",
                            params={"min_value": min_num, "max_value": max_num},
                            confidence=0.7,
                            reason=f"Column values range from {min_num} to {max_num}",
                            severity_suggestion="medium",
                        )
                    )
            except (ValueError, TypeError):
                pass

        return suggestions

    def _suggest_type_rules(
        self,
        column: dict[str, Any],
        schema_column: dict[str, Any] | None = None,
    ) -> list[SuggestedRule]:
        """Suggest type and pattern validators based on data type.

        Args:
            column: Column profile data.
            schema_column: Optional schema column definition.

        Returns:
            List of suggested rules.
        """
        suggestions = []
        col_name = column.get("name", "").lower()
        dtype = column.get("dtype", "").lower()

        # Email detection by column name
        if any(hint in col_name for hint in ("email", "e_mail", "mail")):
            suggestions.append(
                SuggestedRule(
                    column=column.get("name", ""),
                    validator_name="Email",
                    params={},
                    confidence=0.85,
                    reason="Column name suggests email content",
                    severity_suggestion="medium",
                )
            )

        # Phone detection by column name
        if any(hint in col_name for hint in ("phone", "tel", "mobile", "cell")):
            suggestions.append(
                SuggestedRule(
                    column=column.get("name", ""),
                    validator_name="Phone",
                    params={},
                    confidence=0.75,
                    reason="Column name suggests phone number",
                    severity_suggestion="low",
                )
            )

        # URL detection by column name
        if any(hint in col_name for hint in ("url", "link", "website", "href")):
            suggestions.append(
                SuggestedRule(
                    column=column.get("name", ""),
                    validator_name="URL",
                    params={},
                    confidence=0.8,
                    reason="Column name suggests URL content",
                    severity_suggestion="low",
                )
            )

        # Date/datetime type detection
        if dtype in ("datetime64", "date", "timestamp"):
            suggestions.append(
                SuggestedRule(
                    column=column.get("name", ""),
                    validator_name="DateParseable",
                    params={},
                    confidence=0.9,
                    reason=f"Column has {dtype} data type",
                    severity_suggestion="medium",
                )
            )

        # Positive number detection for common column names
        if dtype in ("int64", "int32", "float64", "float32"):
            positive_hints = ("id", "count", "quantity", "amount", "price", "age")
            if any(col_name.endswith(hint) or col_name == hint for hint in positive_hints):
                min_val = column.get("min")
                if min_val is not None:
                    try:
                        if float(min_val) >= 0:
                            suggestions.append(
                                SuggestedRule(
                                    column=column.get("name", ""),
                                    validator_name="Positive",
                                    params={},
                                    confidence=0.75,
                                    reason=f"Column name suggests positive values (min={min_val})",
                                    severity_suggestion="low",
                                )
                            )
                    except (ValueError, TypeError):
                        pass

        return suggestions

    def _suggest_statistical_rules(
        self,
        column: dict[str, Any],
    ) -> list[SuggestedRule]:
        """Suggest statistical validators based on distribution.

        Args:
            column: Column profile data.

        Returns:
            List of suggested rules.
        """
        suggestions = []
        col_name = column.get("name", "")
        mean = column.get("mean")
        std = column.get("std")

        # Suggest Z-score based outlier detection if we have distribution data
        if mean is not None and std is not None and std > 0:
            suggestions.append(
                SuggestedRule(
                    column=col_name,
                    validator_name="ZScore",
                    params={"threshold": 3.0},
                    confidence=0.6,
                    reason=f"Column has mean={mean:.2f}, std={std:.2f}",
                    severity_suggestion="low",
                )
            )

        return suggestions

    async def generate_suggestions(
        self,
        source: Source,
        profile: Profile,
        schema: Schema | None = None,
        *,
        min_confidence: float = 0.5,
    ) -> RuleSuggestionResponse:
        """Generate rule suggestions based on profile data.

        Args:
            source: Source record.
            profile: Profile record.
            schema: Optional schema for additional context.
            min_confidence: Minimum confidence threshold.

        Returns:
            Rule suggestion response.
        """
        suggestions: list[SuggestedRule] = []

        # Get columns from profile
        columns = profile.columns if hasattr(profile, "columns") else []
        if not columns and profile.profile_json:
            columns = profile.profile_json.get("columns", [])

        # Get schema columns for additional context
        schema_columns = {}
        if schema and schema.schema_json:
            schema_columns = schema.schema_json.get("columns", {})

        # Generate suggestions for each column
        for column in columns:
            col_name = column.get("name", "")
            schema_col = schema_columns.get(col_name)

            # Collect all suggestions for this column
            suggestions.extend(self._suggest_null_rules(column))
            suggestions.extend(self._suggest_uniqueness_rules(column))
            suggestions.extend(self._suggest_range_rules(column))
            suggestions.extend(self._suggest_type_rules(column, schema_col))
            suggestions.extend(self._suggest_statistical_rules(column))

        # Filter by confidence threshold
        suggestions = [s for s in suggestions if s.confidence >= min_confidence]

        # Sort by confidence (highest first)
        suggestions.sort(key=lambda s: s.confidence, reverse=True)

        # Count high confidence suggestions
        high_confidence = sum(1 for s in suggestions if s.confidence >= 0.8)

        return RuleSuggestionResponse(
            source_id=source.id,
            source_name=source.name,
            profile_id=profile.id,
            suggestions=suggestions,
            total_suggestions=len(suggestions),
            high_confidence_count=high_confidence,
            generated_at=datetime.utcnow(),
        )

    async def apply_suggestions(
        self,
        source: Source,
        suggestions: list[SuggestedRule],
        *,
        rule_name: str | None = None,
        rule_description: str | None = None,
    ) -> ApplyRulesResponse:
        """Apply selected rule suggestions to create validation rules.

        Args:
            source: Source record.
            suggestions: Selected suggestions to apply.
            rule_name: Optional name for the rule set.
            rule_description: Optional description.

        Returns:
            Apply rules response.
        """
        # Build rules YAML from suggestions
        rules_dict: dict[str, Any] = {"columns": {}}

        validators_applied = []
        for suggestion in suggestions:
            col_name = suggestion.column
            validator_name = suggestion.validator_name

            if col_name not in rules_dict["columns"]:
                rules_dict["columns"][col_name] = {}

            # Add validator with params
            if suggestion.params:
                rules_dict["columns"][col_name][validator_name.lower()] = suggestion.params
            else:
                rules_dict["columns"][col_name][validator_name.lower()] = True

            validators_applied.append(validator_name)

        # Create YAML string
        import yaml
        rules_yaml = yaml.dump(rules_dict, default_flow_style=False)

        # Create rule record
        final_name = rule_name or f"Auto-generated rules for {source.name}"
        final_description = rule_description or (
            f"Automatically generated from profile analysis. "
            f"Includes {len(suggestions)} validators."
        )

        # Deactivate existing rules
        existing_rules = await self.rule_repo.get_for_source(
            source.id, active_only=True
        )
        for rule in existing_rules:
            rule.is_active = False

        # Create new rule
        rule = await self.rule_repo.create(
            source_id=source.id,
            name=final_name,
            description=final_description,
            rules_yaml=rules_yaml,
            rules_json=rules_dict,
            is_active=True,
        )

        await self.session.commit()

        return ApplyRulesResponse(
            source_id=source.id,
            rule_id=rule.id,
            rule_name=rule.name,
            applied_count=len(suggestions),
            validators=list(set(validators_applied)),
            created_at=rule.created_at,
        )
