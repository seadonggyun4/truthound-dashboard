"""Authorization and permission registry for the dashboard control-plane."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from truthound_dashboard.db import Membership, Permission, Role, RolePermission


@dataclass(frozen=True)
class PermissionDefinition:
    key: str
    category: str
    description: str


SYSTEM_PERMISSION_DEFINITIONS: tuple[PermissionDefinition, ...] = (
    PermissionDefinition("sources:read", "sources", "Read source definitions"),
    PermissionDefinition("sources:write", "sources", "Create and update sources"),
    PermissionDefinition("validations:read", "validations", "Read validation history"),
    PermissionDefinition("validations:write", "validations", "Run and manage validations"),
    PermissionDefinition("incidents:read", "incidents", "Read incidents and alerts"),
    PermissionDefinition("incidents:write", "incidents", "Acknowledge, resolve, and assign incidents"),
    PermissionDefinition("artifacts:read", "artifacts", "Read reports and Data Docs artifacts"),
    PermissionDefinition("artifacts:write", "artifacts", "Generate and manage artifacts"),
    PermissionDefinition("plugins:read", "plugins", "Read plugin registry inventory"),
    PermissionDefinition("plugins:write", "plugins", "Install and enable plugins"),
    PermissionDefinition("observability:read", "observability", "Read observability state"),
    PermissionDefinition("views:write", "views", "Create and edit saved views"),
    PermissionDefinition("users:read", "rbac", "Read users"),
    PermissionDefinition("roles:read", "rbac", "Read roles"),
    PermissionDefinition("permissions:read", "rbac", "Read permission registry"),
    PermissionDefinition("queues:read", "incidents", "Read incident queues"),
    PermissionDefinition("queues:write", "incidents", "Create and manage incident queues"),
)

SYSTEM_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": [definition.key for definition in SYSTEM_PERMISSION_DEFINITIONS],
    "operator": [
        "sources:read",
        "sources:write",
        "validations:read",
        "validations:write",
        "incidents:read",
        "incidents:write",
        "artifacts:read",
        "artifacts:write",
        "plugins:read",
        "observability:read",
        "views:write",
        "queues:read",
        "queues:write",
    ],
    "viewer": [
        "sources:read",
        "validations:read",
        "incidents:read",
        "artifacts:read",
        "plugins:read",
        "observability:read",
        "queues:read",
        "permissions:read",
        "roles:read",
    ],
}

SYSTEM_ROLE_DESCRIPTIONS: dict[str, str] = {
    "admin": "System administrator role",
    "operator": "Operational user role",
    "viewer": "Read-only viewer role",
}


class AuthorizationService:
    """Normalized RBAC service."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ensure_seeded(self) -> dict[str, Role]:
        permission_result = await self.session.execute(
            select(Permission).order_by(Permission.key.asc())
        )
        permissions = {permission.key: permission for permission in permission_result.scalars().all()}

        for definition in SYSTEM_PERMISSION_DEFINITIONS:
            permission = permissions.get(definition.key)
            if permission is None:
                permission = Permission(
                    key=definition.key,
                    category=definition.category,
                    description=definition.description,
                    is_system=True,
                )
                self.session.add(permission)
                await self.session.flush()
                permissions[definition.key] = permission
            else:
                permission.category = definition.category
                permission.description = definition.description
                permission.is_system = True

        role_result = await self.session.execute(
            select(Role)
            .options(
                selectinload(Role.permission_links).selectinload(RolePermission.permission),
            )
            .where(Role.name.in_(tuple(SYSTEM_ROLE_PERMISSIONS.keys())))
            .order_by(Role.name.asc())
        )
        roles = {role.name: role for role in role_result.scalars().all()}

        for role_name, permission_keys in SYSTEM_ROLE_PERMISSIONS.items():
            role = roles.get(role_name)
            if role is None:
                role = Role(
                    name=role_name,
                    description=SYSTEM_ROLE_DESCRIPTIONS[role_name],
                    is_system=True,
                )
                self.session.add(role)
                await self.session.flush()
                await self.session.refresh(role)
                roles[role_name] = role
                role.permission_links = []

            role.description = SYSTEM_ROLE_DESCRIPTIONS[role_name]
            role.is_system = True

            current_links = {
                link.permission.key: link
                for link in role.permission_links
                if link.permission is not None
            }
            desired_keys = set(permission_keys)

            for key, link in current_links.items():
                if key not in desired_keys:
                    await self.session.delete(link)

            for key in desired_keys:
                if key in current_links:
                    continue
                permission = permissions[key]
                self.session.add(
                    RolePermission(
                        role_id=role.id,
                        permission_id=permission.id,
                    )
                )

        await self.session.flush()

        refreshed_roles = await self.session.execute(
            select(Role)
            .options(
                selectinload(Role.permission_links).selectinload(RolePermission.permission),
            )
            .where(Role.name.in_(tuple(SYSTEM_ROLE_PERMISSIONS.keys())))
            .order_by(Role.name.asc())
        )
        return {role.name: role for role in refreshed_roles.scalars().all()}

    async def list_permissions(self) -> list[Permission]:
        await self.ensure_seeded()
        result = await self.session.execute(select(Permission).order_by(Permission.key.asc()))
        return list(result.scalars().all())

    async def list_roles(self) -> list[Role]:
        await self.ensure_seeded()
        result = await self.session.execute(
            select(Role)
            .options(selectinload(Role.permission_links).selectinload(RolePermission.permission))
            .order_by(Role.name.asc())
        )
        return list(result.scalars().all())

    def permission_keys_for_role(self, role: Role) -> list[str]:
        return sorted(
            {
                link.permission.key
                for link in role.permission_links
                if link.permission is not None
            }
        )

    async def effective_permission_keys(self, *, user_id: str, workspace_id: str) -> set[str]:
        result = await self.session.execute(
            select(Membership)
            .options(
                selectinload(Membership.role)
                .selectinload(Role.permission_links)
                .selectinload(RolePermission.permission)
            )
            .where(Membership.user_id == user_id, Membership.workspace_id == workspace_id)
        )
        membership = result.scalar_one_or_none()
        if membership is None:
            return set()
        return set(self.permission_keys_for_role(membership.role))

    async def has_permission(self, *, user_id: str, workspace_id: str, permission_key: str) -> bool:
        return permission_key in await self.effective_permission_keys(
            user_id=user_id,
            workspace_id=workspace_id,
        )
