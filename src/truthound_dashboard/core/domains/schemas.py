"""Schema domain services and repositories."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db import BaseRepository, Schema

from ..datasource_factory import SourceType
from ..truthound_adapter import get_adapter
from .source_io import get_async_data_input_from_source, get_data_input_from_source
from .sources import SourceRepository


class SchemaRepository(BaseRepository[Schema]):
    model = Schema

    async def get_active_for_source(self, source_id: str) -> Schema | None:
        result = await self.session.execute(
            select(Schema)
            .where(Schema.source_id == source_id)
            .where(Schema.is_active)
            .order_by(Schema.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def deactivate_for_source(self, source_id: str) -> None:
        result = await self.session.execute(
            select(Schema).where(Schema.source_id == source_id).where(Schema.is_active)
        )
        for schema in result.scalars().all():
            schema.is_active = False


class SchemaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.source_repo = SourceRepository(session)
        self.schema_repo = SchemaRepository(session)
        self.adapter = get_adapter()

    async def learn_schema(
        self,
        source_id: str,
        *,
        infer_constraints: bool = True,
        categorical_threshold: int | None = None,
        sample_size: int | None = None,
    ) -> Schema:
        source = await self.source_repo.get_by_id(source_id)
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")

        if SourceType.is_async_type(source.type):
            data_input = await get_async_data_input_from_source(source, self.session)
        else:
            data_input = await get_data_input_from_source(source, self.session)

        result = await self.adapter.learn(
            data_input,
            infer_constraints=infer_constraints,
            categorical_threshold=categorical_threshold,
            sample_size=sample_size,
        )

        await self.schema_repo.deactivate_for_source(source_id)
        return await self.schema_repo.create(
            source_id=source_id,
            schema_yaml=result.schema_yaml,
            schema_json=result.schema,
            row_count=result.row_count,
            column_count=result.column_count,
            is_active=True,
        )

    async def get_schema(self, source_id: str) -> Schema | None:
        return await self.schema_repo.get_active_for_source(source_id)

    async def update_schema(self, source_id: str, schema_yaml: str) -> Schema | None:
        import yaml

        schema = await self.schema_repo.get_active_for_source(source_id)
        if schema is None:
            return None
        try:
            schema_json = yaml.safe_load(schema_yaml)
        except yaml.YAMLError:
            schema_json = None

        schema.schema_yaml = schema_yaml
        schema.schema_json = schema_json
        await self.session.flush()
        await self.session.refresh(schema)
        return schema


__all__ = ["SchemaRepository", "SchemaService"]
