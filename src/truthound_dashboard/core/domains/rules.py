"""Rule domain services and repositories."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db import BaseRepository, Rule

from .sources import SourceRepository


class RuleRepository(BaseRepository[Rule]):
    model = Rule

    async def get_for_source(
        self,
        source_id: str,
        *,
        limit: int = 50,
        active_only: bool = False,
    ) -> Sequence[Rule]:
        filters = [Rule.source_id == source_id]
        if active_only:
            filters.append(Rule.is_active)
        return await self.list(
            limit=limit,
            filters=filters,
            order_by=Rule.created_at.desc(),
        )

    async def get_active_for_source(self, source_id: str) -> Rule | None:
        result = await self.session.execute(
            select(Rule)
            .where(Rule.source_id == source_id)
            .where(Rule.is_active)
            .order_by(Rule.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def deactivate_for_source(self, source_id: str) -> int:
        result = await self.session.execute(
            select(Rule).where(Rule.source_id == source_id).where(Rule.is_active)
        )
        rules = result.scalars().all()
        for rule in rules:
            rule.is_active = False
        return len(rules)


class RuleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.source_repo = SourceRepository(session)
        self.rule_repo = RuleRepository(session)

    async def get_rule(self, rule_id: str) -> Rule | None:
        return await self.rule_repo.get_by_id(rule_id)

    async def get_rules_for_source(
        self,
        source_id: str,
        *,
        limit: int = 50,
        active_only: bool = False,
    ) -> Sequence[Rule]:
        return await self.rule_repo.get_for_source(
            source_id,
            limit=limit,
            active_only=active_only,
        )

    async def get_active_rule(self, source_id: str) -> Rule | None:
        return await self.rule_repo.get_active_for_source(source_id)

    async def create_rule(
        self,
        source_id: str,
        *,
        rules_yaml: str,
        name: str = "Default Rules",
        description: str | None = None,
        version: str | None = None,
        activate: bool = True,
    ) -> Rule:
        import yaml

        source = await self.source_repo.get_by_id(source_id)
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")

        try:
            rules_json = yaml.safe_load(rules_yaml)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML: {exc}") from exc

        if activate:
            await self.rule_repo.deactivate_for_source(source_id)

        return await self.rule_repo.create(
            source_id=source_id,
            name=name,
            description=description,
            rules_yaml=rules_yaml,
            rules_json=rules_json,
            is_active=activate,
            version=version,
        )

    async def update_rule(
        self,
        rule_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        rules_yaml: str | None = None,
        version: str | None = None,
        is_active: bool | None = None,
    ) -> Rule | None:
        import yaml

        rule = await self.rule_repo.get_by_id(rule_id)
        if rule is None:
            return None

        if name is not None:
            rule.name = name
        if description is not None:
            rule.description = description
        if version is not None:
            rule.version = version
        if rules_yaml is not None:
            try:
                rules_json = yaml.safe_load(rules_yaml)
            except yaml.YAMLError as exc:
                raise ValueError(f"Invalid YAML: {exc}") from exc
            rule.rules_yaml = rules_yaml
            rule.rules_json = rules_json
        if is_active is not None:
            if is_active and not rule.is_active:
                await self.rule_repo.deactivate_for_source(rule.source_id)
            rule.is_active = is_active

        await self.session.flush()
        await self.session.refresh(rule)
        return rule

    async def delete_rule(self, rule_id: str) -> bool:
        return await self.rule_repo.delete(rule_id)

    async def activate_rule(self, rule_id: str) -> Rule | None:
        rule = await self.rule_repo.get_by_id(rule_id)
        if rule is None:
            return None
        await self.rule_repo.deactivate_for_source(rule.source_id)
        rule.is_active = True
        await self.session.flush()
        await self.session.refresh(rule)
        return rule


__all__ = ["RuleRepository", "RuleService"]
