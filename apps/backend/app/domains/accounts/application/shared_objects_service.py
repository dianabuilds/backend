from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shared_objects import SharedObject


async def grant_access(
    db: AsyncSession,
    *,
    object_type: str,
    object_id: UUID,
    account_id: UUID,
    permissions: str,
) -> SharedObject:
    res = await db.execute(
        select(SharedObject).where(
            SharedObject.object_type == object_type,
            SharedObject.object_id == object_id,
            SharedObject.account_id == account_id,
        )
    )
    shared = res.scalars().first()
    if shared:
        shared.permissions = permissions
    else:
        shared = SharedObject(
            object_type=object_type,
            object_id=object_id,
            account_id=account_id,
            permissions=permissions,
        )
        db.add(shared)
    await db.commit()
    await db.refresh(shared)
    return shared


async def revoke_access(
    db: AsyncSession,
    *,
    object_type: str,
    object_id: UUID,
    account_id: UUID,
) -> None:
    await db.execute(
        delete(SharedObject).where(
            SharedObject.object_type == object_type,
            SharedObject.object_id == object_id,
            SharedObject.account_id == account_id,
        )
    )
    await db.commit()


async def has_access(
    db: AsyncSession,
    *,
    object_type: str,
    object_id: UUID,
    account_id: UUID,
    permission: str,
) -> bool:
    res = await db.execute(
        select(SharedObject).where(
            SharedObject.object_type == object_type,
            SharedObject.object_id == object_id,
            SharedObject.account_id == account_id,
        )
    )
    shared = res.scalars().first()
    if not shared:
        return False
    perms = {p.strip() for p in shared.permissions.split(",") if p.strip()}
    return permission in perms or "*" in perms
