from __future__ import annotations

import re
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.domains.accounts.infrastructure.dao import AccountDAO, AccountMemberDAO
from app.domains.accounts.infrastructure.models import Account, AccountMember
from app.domains.users.infrastructure.models.user import User
from app.providers.db.pagination import (
    PageQuery,
    apply_pagination,
    apply_sorting,
    build_cursor_for_last_item,
    decode_cursor,
    fetch_page,
)
from app.providers.db.session import get_db
from app.schemas.accounts import (
    AccountCursorPage,
    AccountIn,
    AccountMemberIn,
    AccountOut,
    AccountRole,
    AccountUpdate,
    AccountWithRoleOut,
)

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="bearerAuth")


async def _auth_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Security(bearer_scheme)  # noqa: B008
    ] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> User:
    from app.security import auth_user

    return await auth_user(request, credentials, db)


async def require_account_editor(
    account_id: UUID,
    user: Annotated[User, Depends(_auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> AccountMember | None:
    """Ensure the current user has editor or owner rights in the account."""
    m = await AccountMemberDAO.get(db, account_id=account_id, user_id=user.id)
    if not (user.role == "admin" or (m and m.role in (AccountRole.owner, AccountRole.editor))):
        raise HTTPException(status_code=403, detail="Forbidden")
    return m


async def require_account_owner(
    account_id: UUID,
    user: Annotated[User, Depends(_auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> AccountMember | None:
    """Ensure the current user is an owner of the account."""
    m = await AccountMemberDAO.get(db, account_id=account_id, user_id=user.id)
    if not (user.role == "admin" or (m and m.role == AccountRole.owner)):
        raise HTTPException(status_code=403, detail="Forbidden")
    return m


async def require_account_viewer(
    account_id: UUID,
    user: Annotated[User, Depends(_auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> AccountMember | None:
    """Ensure the current user has at least viewer rights in the account."""
    m = await AccountMemberDAO.get(db, account_id=account_id, user_id=user.id)
    if not (
        user.role == "admin"
        or (m and m.role in (AccountRole.owner, AccountRole.editor, AccountRole.viewer))
    ):
        raise HTTPException(status_code=403, detail="Forbidden")
    return m


async def require_account_guest(
    account_id: UUID,
    user: Annotated[User, Depends(_auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> AccountMember | None:
    """Ensure the current user is a member of the account."""
    m = await AccountMemberDAO.get(db, account_id=account_id, user_id=user.id)
    if not (user.role == "admin" or m):
        raise HTTPException(status_code=403, detail="Forbidden")
    return m


def scope_by_account(query: Select, account_id: UUID) -> Select:
    """Filter a SQLAlchemy query by account identifier if possible."""
    entity = query.column_descriptions[0]["entity"]
    if hasattr(entity, "account_id"):
        query = query.where(entity.account_id == account_id)
    return query


SLUG_RE = re.compile(r"^[a-z0-9-]+$")


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", text.lower())
    return re.sub(r"-+", "-", slug).strip("-")


class AccountService:
    @staticmethod
    async def create(db: AsyncSession, *, data: AccountIn, owner: User) -> Account:
        slug = data.slug or _slugify(data.name)
        if not SLUG_RE.fullmatch(slug):
            raise HTTPException(status_code=400, detail="Invalid slug")
        res = await db.execute(select(Account).where(Account.slug == slug))
        if res.scalars().first():
            raise HTTPException(status_code=400, detail="Slug already exists")
        res = await db.execute(
            select(Account).where(Account.owner_user_id == owner.id, Account.name == data.name)
        )
        if res.scalars().first():
            raise HTTPException(status_code=400, detail="Name already exists")
        account = Account(
            name=data.name,
            slug=slug,
            owner_user_id=owner.id,
            settings_json=data.settings.model_dump(),
            kind=data.kind,
            is_system=data.is_system,
        )
        db.add(account)
        db.add(AccountMember(account=account, user_id=owner.id, role=AccountRole.owner))
        await db.commit()
        await db.refresh(account)
        return account

    @staticmethod
    async def list_for_user(db: AsyncSession, user: User) -> list[tuple[Account, AccountRole]]:
        stmt = (
            select(Account, AccountMember.role)
            .join(AccountMember)
            .where(AccountMember.user_id == user.id)
        )
        result = await db.execute(stmt)
        return [(ws, role) for ws, role in result.all()]

    @staticmethod
    async def get_for_user(db: AsyncSession, account_id: UUID, user: User) -> Account:
        account = await AccountDAO.get(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        if user.role != "admin":
            member = await AccountMemberDAO.get(db, account_id=account_id, user_id=user.id)
            if not member:
                raise HTTPException(status_code=403, detail="Forbidden")
        return account

    @staticmethod
    async def update(db: AsyncSession, account_id: UUID, data: AccountUpdate) -> Account:
        account = await AccountDAO.get(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        if data.name is not None and data.name != account.name:
            res = await db.execute(
                select(Account).where(
                    Account.owner_user_id == account.owner_user_id,
                    Account.name == data.name,
                    Account.id != account_id,
                )
            )
            if res.scalars().first():
                raise HTTPException(status_code=400, detail="Name already exists")
            account.name = data.name
        if data.slug is not None and data.slug != account.slug:
            if not SLUG_RE.fullmatch(data.slug):
                raise HTTPException(status_code=400, detail="Invalid slug")
            res = await db.execute(
                select(Account).where(Account.slug == data.slug, Account.id != account_id)
            )
            if res.scalars().first():
                raise HTTPException(status_code=400, detail="Slug already exists")
            account.slug = data.slug
        if data.settings is not None:
            account.settings_json = data.settings.model_dump()
        if data.kind is not None:
            account.kind = data.kind
        if data.is_system is not None:
            account.is_system = data.is_system
        await db.commit()
        await db.refresh(account)
        return account

    @staticmethod
    async def delete(db: AsyncSession, account_id: UUID) -> None:
        account = await AccountDAO.get(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        await db.delete(account)
        await db.commit()

    @staticmethod
    async def add_member(
        db: AsyncSession, account_id: UUID, data: AccountMemberIn
    ) -> AccountMember:
        existing = await AccountMemberDAO.get(db, account_id=account_id, user_id=data.user_id)
        if existing:
            raise HTTPException(status_code=400, detail="Member already exists")
        member = await AccountMemberDAO.add(
            db,
            account_id=account_id,
            user_id=data.user_id,
            role=data.role,
        )
        await db.commit()
        await db.refresh(member)
        return member

    @staticmethod
    async def update_member(
        db: AsyncSession, account_id: UUID, user_id: UUID, role: AccountRole
    ) -> AccountMember:
        member = await AccountMemberDAO.update_role(
            db, account_id=account_id, user_id=user_id, role=role
        )
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        await db.commit()
        await db.refresh(member)
        return member

    @staticmethod
    async def remove_member(db: AsyncSession, account_id: UUID, user_id: UUID) -> None:
        member = await AccountMemberDAO.get(db, account_id=account_id, user_id=user_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        await AccountMemberDAO.remove(db, account_id=account_id, user_id=user_id)
        await db.commit()

    @staticmethod
    async def list_members(db: AsyncSession, account_id: UUID) -> list[AccountMember]:
        res = await db.execute(select(AccountMember).where(AccountMember.account_id == account_id))
        return res.scalars().all()

    @staticmethod
    async def list_paginated(
        db: AsyncSession,
        *,
        user: User,
        pq: PageQuery,
    ) -> AccountCursorPage:
        stmt = select(Account).join(AccountMember).where(AccountMember.user_id == user.id)
        stmt = apply_sorting(stmt, model=Account, sort_field=pq.sort, order=pq.order)
        cursor = decode_cursor(pq.cursor) if pq.cursor else None
        stmt = apply_pagination(
            stmt,
            model=Account,
            cursor=cursor,
            sort_field=pq.sort,
            order=pq.order,
        )
        items, has_next = await fetch_page(stmt, session=db, limit=pq.limit)
        next_cursor = (
            build_cursor_for_last_item(items[-1], pq.sort, pq.order) if has_next and items else None
        )
        roles: dict[UUID, AccountRole] = {}
        if items:
            res = await db.execute(
                select(AccountMember.account_id, AccountMember.role).where(
                    AccountMember.user_id == user.id,
                    AccountMember.account_id.in_([ws.id for ws in items]),
                )
            )
            roles = {row.account_id: row.role for row in res.all()}
        out: list[AccountWithRoleOut] = []
        for ws in items:
            data = AccountOut.model_validate(ws, from_attributes=True)
            out.append(
                AccountWithRoleOut(
                    **data.model_dump(exclude={"role"}),
                    role=roles.get(ws.id, AccountRole.viewer),
                )
            )
        return AccountCursorPage(
            limit=pq.limit,
            sort=pq.sort,
            order=pq.order,
            items=out,
            next_cursor=next_cursor,
        )
