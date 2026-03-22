"""Profile domain services and repositories."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db import BaseRepository, Profile

from ..datasource_factory import SourceType
from ..truthound_adapter import get_adapter
from .source_io import get_async_data_input_from_source, get_data_input_from_source
from .sources import SourceRepository


class ProfileRepository(BaseRepository[Profile]):
    model = Profile

    async def get_for_source(
        self,
        source_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[Profile]:
        return await self.list(
            offset=offset,
            limit=limit,
            filters=[Profile.source_id == source_id],
            order_by=Profile.created_at.desc(),
        )

    async def get_latest_for_source(self, source_id: str) -> Profile | None:
        result = await self.session.execute(
            select(Profile)
            .where(Profile.source_id == source_id)
            .order_by(Profile.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.source_repo = SourceRepository(session)
        self.profile_repo = ProfileRepository(session)
        self.adapter = get_adapter()

    async def profile_source(
        self,
        source_id: str,
        *,
        sample_size: int | None = None,
        include_patterns: bool = True,
        save: bool = True,
    ) -> Profile:
        source = await self.source_repo.get_by_id(source_id)
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")

        if SourceType.is_async_type(source.type):
            data_input = await get_async_data_input_from_source(source, self.session)
        else:
            data_input = await get_data_input_from_source(source, self.session)

        result = await self.adapter.profile(
            data_input,
            sample_size=sample_size,
            include_patterns=include_patterns,
        )
        if save:
            return await self.profile_repo.create(
                source_id=source_id,
                profile_json=result.to_dict(),
                row_count=result.row_count,
                column_count=result.column_count,
                size_bytes=result.size_bytes or result.estimated_memory_bytes,
            )

        return Profile(
            source_id=source_id,
            profile_json=result.to_dict(),
            row_count=result.row_count,
            column_count=result.column_count,
            size_bytes=result.size_bytes or result.estimated_memory_bytes,
        )

    async def profile_source_advanced(
        self,
        source_id: str,
        *,
        config: dict[str, Any] | None = None,
        save: bool = True,
    ) -> Profile:
        source = await self.source_repo.get_by_id(source_id)
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")

        if SourceType.is_async_type(source.type):
            data_input = await get_async_data_input_from_source(source, self.session)
        else:
            data_input = await get_data_input_from_source(source, self.session)

        result = await self.adapter.profile_advanced(
            data_input,
            config=config,
        )
        if save:
            return await self.profile_repo.create(
                source_id=source_id,
                profile_json=result.to_dict(),
                row_count=result.row_count,
                column_count=result.column_count,
                size_bytes=result.size_bytes or result.estimated_memory_bytes,
            )

        return Profile(
            source_id=source_id,
            profile_json=result.to_dict(),
            row_count=result.row_count,
            column_count=result.column_count,
            size_bytes=result.size_bytes or result.estimated_memory_bytes,
        )

    async def generate_rules_from_profile(
        self,
        source_id: str,
        *,
        strictness: str = "medium",
        preset: str = "default",
        include_categories: list[str] | None = None,
        exclude_categories: list[str] | None = None,
        profile_if_needed: bool = True,
        sample_size: int | None = None,
    ) -> dict[str, Any]:
        source = await self.source_repo.get_by_id(source_id)
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")

        profile = await self.profile_repo.get_latest_for_source(source_id)
        if profile is None:
            if not profile_if_needed:
                raise ValueError(
                    f"No profile found for source '{source_id}'. "
                    "Run profile_source() first or set profile_if_needed=True."
                )
            profile = await self.profile_source(
                source_id,
                sample_size=sample_size,
                include_patterns=True,
                save=True,
            )

        result = await self.adapter.generate_suite(
            profile.profile_json,
            strictness=strictness,
            preset=preset,
            include=include_categories,
            exclude=exclude_categories,
        )
        return {
            "source_id": source_id,
            "profile_id": str(profile.id) if profile.id else None,
            "rules": result.rules,
            "rule_count": result.rule_count,
            "categories": result.categories,
            "strictness": result.strictness,
            "yaml_content": result.yaml_content,
            "json_content": result.json_content,
        }

    async def get(self, profile_id: str) -> Profile | None:
        return await self.profile_repo.get_by_id(profile_id)

    async def get_latest(self, source_id: str) -> Profile | None:
        return await self.profile_repo.get_latest_for_source(source_id)

    async def get_latest_profile(self, source_id: str) -> Profile | None:
        return await self.profile_repo.get_latest_for_source(source_id)

    async def list_profiles(
        self,
        source_id: str,
        *,
        limit: int = 20,
    ) -> Sequence[Profile]:
        return await self.profile_repo.get_for_source(source_id, limit=limit)

    async def compare_profiles(
        self,
        source_id: str,
        profile_id_1: str | None = None,
        profile_id_2: str | None = None,
    ) -> dict[str, Any]:
        profiles = await self.profile_repo.get_for_source(source_id, limit=10)
        if len(profiles) < 2:
            raise ValueError(
                f"Need at least 2 profiles to compare. Source '{source_id}' has {len(profiles)}."
            )

        if profile_id_2 is None:
            profile_2 = profiles[0]
        else:
            profile_2 = await self.profile_repo.get_by_id(profile_id_2)
            if profile_2 is None:
                raise ValueError(f"Profile '{profile_id_2}' not found")

        if profile_id_1 is None:
            profile_1 = profiles[1]
        else:
            profile_1 = await self.profile_repo.get_by_id(profile_id_1)
            if profile_1 is None:
                raise ValueError(f"Profile '{profile_id_1}' not found")

        return self._compare_profile_data(
            profile_1.profile_json,
            profile_2.profile_json,
            profile_1_id=str(profile_1.id),
            profile_2_id=str(profile_2.id),
        )

    def _compare_profile_data(
        self,
        profile_1: dict[str, Any],
        profile_2: dict[str, Any],
        profile_1_id: str,
        profile_2_id: str,
    ) -> dict[str, Any]:
        changes = []
        column_diffs = []
        cols_1 = {column["name"]: column for column in profile_1.get("columns", [])}
        cols_2 = {column["name"]: column for column in profile_2.get("columns", [])}
        added_cols = set(cols_2.keys()) - set(cols_1.keys())
        removed_cols = set(cols_1.keys()) - set(cols_2.keys())
        common_cols = set(cols_1.keys()) & set(cols_2.keys())

        for col in added_cols:
            changes.append({"type": "column_added", "column": col, "details": cols_2[col]})
        for col in removed_cols:
            changes.append({"type": "column_removed", "column": col, "details": cols_1[col]})

        for col in common_cols:
            col_1 = cols_1[col]
            col_2 = cols_2[col]
            col_changes = []
            if col_1.get("inferred_type") != col_2.get("inferred_type"):
                col_changes.append(
                    {
                        "field": "inferred_type",
                        "old": col_1.get("inferred_type"),
                        "new": col_2.get("inferred_type"),
                    }
                )

            old_null = col_1.get("null_ratio", 0)
            new_null = col_2.get("null_ratio", 0)
            if abs(old_null - new_null) > 0.05:
                col_changes.append(
                    {
                        "field": "null_ratio",
                        "old": old_null,
                        "new": new_null,
                        "change": new_null - old_null,
                    }
                )

            old_unique = col_1.get("unique_ratio", 0)
            new_unique = col_2.get("unique_ratio", 0)
            if abs(old_unique - new_unique) > 0.1:
                col_changes.append(
                    {
                        "field": "unique_ratio",
                        "old": old_unique,
                        "new": new_unique,
                        "change": new_unique - old_unique,
                    }
                )

            if col_changes:
                column_diffs.append({"column": col, "changes": col_changes})

        return {
            "profile_1_id": profile_1_id,
            "profile_2_id": profile_2_id,
            "row_count_change": profile_2.get("row_count", 0) - profile_1.get("row_count", 0),
            "column_count_change": profile_2.get("column_count", 0) - profile_1.get("column_count", 0),
            "added_columns": list(added_cols),
            "removed_columns": list(removed_cols),
            "schema_changes": changes,
            "column_diffs": column_diffs,
            "has_breaking_changes": len(removed_cols) > 0
            or any(
                change.get("field") == "inferred_type"
                for diff in column_diffs
                for change in diff.get("changes", [])
            ),
        }


__all__ = ["ProfileRepository", "ProfileService"]
