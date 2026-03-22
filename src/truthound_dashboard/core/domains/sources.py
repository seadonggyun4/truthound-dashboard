"""Source domain services and repositories."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from truthound_dashboard.db import (
    BaseRepository,
    Domain,
    SavedView,
    Source,
    SourceOwnership,
    Team,
    User,
    Validation,
)
from truthound_dashboard.time import utc_now

from ..secrets import LocalEncryptedDbSecretProvider, merge_secret_aware_configs
from .source_io import _has_sensitive_config, _resolve_source_config


class SourceRepository(BaseRepository[Source]):
    model = Source

    async def get_active(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        workspace_id: str | None = None,
    ) -> Sequence[Source]:
        filters = [Source.is_active]
        if workspace_id is not None:
            filters.append(and_(Source.workspace_id == workspace_id))
        return await self.list(offset=offset, limit=limit, filters=filters)

    async def get_by_name(self, name: str, workspace_id: str | None = None) -> Source | None:
        query = select(Source).where(Source.name == name)
        if workspace_id is not None:
            query = query.where(Source.workspace_id == workspace_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class SourceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = SourceRepository(session)
        from .schemas import SchemaRepository
        from .validations import ValidationRepository

        self.schema_repo = SchemaRepository(session)
        self.validation_repo = ValidationRepository(session)
        self.secrets = LocalEncryptedDbSecretProvider(session)

    def _query(self):
        return select(Source).options(
            selectinload(Source.schemas),
            selectinload(Source.validations),
            selectinload(Source.ownership).selectinload(SourceOwnership.owner_user),
            selectinload(Source.ownership).selectinload(SourceOwnership.team),
            selectinload(Source.ownership).selectinload(SourceOwnership.domain),
        )

    async def _saved_view_filters(
        self,
        *,
        workspace_id: str | None,
        saved_view_id: str | None,
    ) -> dict[str, Any]:
        if not workspace_id or not saved_view_id:
            return {}
        result = await self.session.execute(
            select(SavedView).where(
                SavedView.id == saved_view_id,
                SavedView.workspace_id == workspace_id,
                SavedView.scope == "sources",
            )
        )
        view = result.scalar_one_or_none()
        return {} if view is None else (view.filters or {})

    async def _apply_source_filters(
        self,
        *,
        workspace_id: str | None,
        active_only: bool | None = None,
        status: str | None = None,
        search: str | None = None,
        owner_user_id: str | None = None,
        team_id: str | None = None,
        domain_id: str | None = None,
        saved_view_id: str | None = None,
    ) -> list[Any]:
        filters: list[Any] = []
        saved_view_filters = await self._saved_view_filters(
            workspace_id=workspace_id,
            saved_view_id=saved_view_id,
        )
        effective_search = search or saved_view_filters.get("search")
        effective_status = status or saved_view_filters.get("status")
        effective_owner = owner_user_id or saved_view_filters.get("owner_user_id")
        effective_team = team_id or saved_view_filters.get("team_id")
        effective_domain = domain_id or saved_view_filters.get("domain_id")

        if workspace_id is not None:
            filters.append(Source.workspace_id == workspace_id)
        if active_only:
            filters.append(Source.is_active == True)  # noqa: E712
        elif effective_status == "active":
            filters.append(Source.is_active == True)  # noqa: E712
        elif effective_status == "inactive":
            filters.append(Source.is_active == False)  # noqa: E712
        if effective_search:
            filters.append(
                or_(
                    Source.name.ilike(f"%{effective_search}%"),
                    Source.description.ilike(f"%{effective_search}%"),
                )
            )
        if effective_owner:
            filters.append(SourceOwnership.owner_user_id == str(effective_owner))
        if effective_team:
            filters.append(SourceOwnership.team_id == str(effective_team))
        if effective_domain:
            filters.append(SourceOwnership.domain_id == str(effective_domain))
        return filters

    async def get_by_id(self, id: str, *, workspace_id: str | None = None) -> Source | None:
        query = self._query().where(Source.id == id)
        if workspace_id is not None:
            query = query.where(Source.workspace_id == workspace_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        active_only: bool = True,
        workspace_id: str | None = None,
        saved_view_id: str | None = None,
        search: str | None = None,
        status: str | None = None,
        owner_user_id: str | None = None,
        team_id: str | None = None,
        domain_id: str | None = None,
    ) -> Sequence[Source]:
        filters = await self._apply_source_filters(
            workspace_id=workspace_id,
            active_only=active_only,
            status=status,
            search=search,
            owner_user_id=owner_user_id,
            team_id=team_id,
            domain_id=domain_id,
            saved_view_id=saved_view_id,
        )
        query = self._query().outerjoin(SourceOwnership, SourceOwnership.source_id == Source.id)
        for filter_clause in filters:
            query = query.where(filter_clause)
        query = query.order_by(Source.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().unique().all())

    async def count(
        self,
        *,
        active_only: bool = True,
        workspace_id: str | None = None,
        saved_view_id: str | None = None,
        search: str | None = None,
        status: str | None = None,
        owner_user_id: str | None = None,
        team_id: str | None = None,
        domain_id: str | None = None,
    ) -> int:
        filters = await self._apply_source_filters(
            workspace_id=workspace_id,
            active_only=active_only,
            status=status,
            search=search,
            owner_user_id=owner_user_id,
            team_id=team_id,
            domain_id=domain_id,
            saved_view_id=saved_view_id,
        )
        query = select(func.count(func.distinct(Source.id))).select_from(Source)
        query = query.outerjoin(SourceOwnership, SourceOwnership.source_id == Source.id)
        for filter_clause in filters:
            query = query.where(filter_clause)
        result = await self.session.execute(query)
        return int(result.scalar_one() or 0)

    async def materialize_config(self, source: Source) -> dict[str, Any]:
        return await _resolve_source_config(source, self.session)

    async def create(
        self,
        *,
        name: str,
        type: str,
        config: dict[str, Any],
        description: str | None = None,
        workspace_id: str | None = None,
        environment: str = "production",
        created_by: str | None = None,
        owner_user_id: str | None = None,
        team_id: str | None = None,
        domain_id: str | None = None,
    ) -> Source:
        source = await self.repository.create(
            name=name,
            type=type,
            workspace_id=workspace_id,
            environment=environment,
            config={},
            credential_updated_at=utc_now() if _has_sensitive_config(config) else None,
            description=description,
        )
        source.config = await self.secrets.persist_config(
            config=config,
            workspace_id=source.workspace_id or workspace_id or "",
            name_prefix=f"source:{source.id}",
            kind="source",
            created_by=created_by,
        )
        await self._upsert_ownership(
            source=source,
            owner_user_id=owner_user_id,
            team_id=team_id,
            domain_id=domain_id,
        )
        await self.session.refresh(source)
        return source

    async def update(
        self,
        id: str,
        *,
        name: str | None = None,
        config: dict[str, Any] | None = None,
        description: str | None = None,
        is_active: bool | None = None,
        environment: str | None = None,
        workspace_id: str | None = None,
        updated_by: str | None = None,
    ) -> Source | None:
        source = await self.get_by_id(id, workspace_id=workspace_id)
        if source is None:
            return None

        if name is not None:
            source.name = name
        if config is not None:
            merged = merge_secret_aware_configs(source.config or {}, config)
            source.config = await self.secrets.persist_config(
                config=merged,
                workspace_id=source.workspace_id or workspace_id or "",
                name_prefix=f"source:{source.id}",
                kind="source",
                created_by=updated_by,
            )
            source.config_version = (source.config_version or 0) + 1
            if _has_sensitive_config(config):
                source.credential_updated_at = utc_now()
        if description is not None:
            source.description = description
        if is_active is not None:
            source.is_active = is_active
        if environment is not None:
            source.environment = environment

        await self.session.flush()
        await self.session.refresh(source)
        return source

    async def rotate_credentials(
        self,
        id: str,
        *,
        credentials: dict[str, Any],
        workspace_id: str | None = None,
    ) -> Source | None:
        source = await self.get_by_id(id, workspace_id=workspace_id)
        if source is None:
            return None
        merged = merge_secret_aware_configs(source.config or {}, credentials)
        source.config = await self.secrets.persist_config(
            config=merged,
            workspace_id=source.workspace_id or workspace_id or "",
            name_prefix=f"source:{source.id}",
            kind="source",
        )
        source.config_version = (source.config_version or 0) + 1
        source.credential_updated_at = utc_now()
        await self.session.flush()
        await self.session.refresh(source)
        return source

    async def _upsert_ownership(
        self,
        *,
        source: Source,
        owner_user_id: str | None = None,
        team_id: str | None = None,
        domain_id: str | None = None,
    ) -> SourceOwnership:
        if owner_user_id is not None:
            owner = await self.session.get(User, owner_user_id)
            if owner is None:
                raise ValueError("Owner user not found")
        if team_id is not None:
            team = await self.session.get(Team, team_id)
            if team is None:
                raise ValueError("Team not found")
        if domain_id is not None:
            domain = await self.session.get(Domain, domain_id)
            if domain is None:
                raise ValueError("Domain not found")

        result = await self.session.execute(
            select(SourceOwnership).where(SourceOwnership.source_id == source.id)
        )
        ownership = result.scalar_one_or_none()
        if ownership is None:
            ownership = SourceOwnership(
                source_id=source.id,
                workspace_id=source.workspace_id or "",
            )
            self.session.add(ownership)
        ownership.workspace_id = source.workspace_id or ""
        ownership.owner_user_id = owner_user_id
        ownership.team_id = team_id
        ownership.domain_id = domain_id
        await self.session.flush()
        await self.session.refresh(ownership)
        return ownership

    async def get_ownership(self, *, source_id: str, workspace_id: str | None = None) -> SourceOwnership | None:
        source = await self.get_by_id(source_id, workspace_id=workspace_id)
        if source is None:
            return None
        result = await self.session.execute(
            select(SourceOwnership)
            .options(
                selectinload(SourceOwnership.owner_user),
                selectinload(SourceOwnership.team),
                selectinload(SourceOwnership.domain),
            )
            .where(SourceOwnership.source_id == source.id)
        )
        return result.scalar_one_or_none()

    async def set_ownership(
        self,
        *,
        source_id: str,
        workspace_id: str | None = None,
        owner_user_id: str | None = None,
        team_id: str | None = None,
        domain_id: str | None = None,
    ) -> SourceOwnership | None:
        source = await self.get_by_id(source_id, workspace_id=workspace_id)
        if source is None:
            return None
        return await self._upsert_ownership(
            source=source,
            owner_user_id=owner_user_id,
            team_id=team_id,
            domain_id=domain_id,
        )

    async def delete(self, id: str) -> bool:
        return await self.repository.delete(id)

    async def get_schema(self, source_id: str):
        return await self.schema_repo.get_active_for_source(source_id)

    async def get_validations(
        self,
        source_id: str,
        *,
        limit: int = 20,
    ) -> Sequence[Validation]:
        validations, _ = await self.validation_repo.get_for_source(source_id, limit=limit)
        return validations


__all__ = ["SourceRepository", "SourceService"]
