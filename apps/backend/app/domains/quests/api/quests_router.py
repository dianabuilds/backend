# ruff: noqa: B008, B904
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import (
    assert_owner_or_role,
    get_current_user,
    get_preview_context,
)
from app.core.db.session import get_db
from app.core.preview import PreviewContext

# правила доступа и геймплей вынесены в домен quests
from app.domains.navigation.application.navigation_cache_service import (
    NavigationCacheService,
)
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.quests.infrastructure.models.quest_models import (
    Quest,
    QuestPurchase,
)
from app.domains.quests.schemas import (
    QuestBuyIn,
    QuestCreate,
    QuestOut,
    QuestProgressOut,
    QuestUpdate,
)
from app.domains.users.infrastructure.models.user import User
from app.schemas.node import NodeOut

navcache = NavigationCacheService(CoreCacheAdapter())

router = APIRouter(prefix="/quests", tags=["quests"])


@router.get("", response_model=list[QuestOut], summary="List quests")
async def list_quests(workspace_id: UUID, db: AsyncSession = Depends(get_db)):
    """Return all published quests."""
    from app.domains.quests.queries import list_public

    return await list_public(db, workspace_id=workspace_id)


@router.get("/search", response_model=list[QuestOut], summary="Search quests")
async def search_quests(
    workspace_id: UUID,
    q: str | None = None,
    tags: str | None = Query(None),
    author_id: UUID | None = None,
    free_only: bool = False,
    premium_only: bool = False,
    sort_by: str = "new",
    page: int = 1,
    per_page: int = 10,
    db: AsyncSession = Depends(get_db),
):
    from app.domains.quests.queries import search

    tag_list = [t for t in (tags.split(",") if tags else []) if t]
    return await search(
        db,
        q=q,
        tags=tag_list,
        author_id=author_id,
        free_only=free_only,
        premium_only=premium_only,
        sort_by=sort_by,
        page=page,
        per_page=per_page,
        workspace_id=workspace_id,
    )


@router.get("/{slug}", response_model=QuestOut, summary="Get quest")
async def get_quest(
    slug: str,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a quest by slug, ensuring access permissions."""
    from app.domains.quests.queries import get_for_view

    try:
        quest = await get_for_view(
            db, slug=slug, user=current_user, workspace_id=workspace_id
        )
    except ValueError as err:
        raise HTTPException(status_code=404, detail="Quest not found") from err
    except PermissionError as err:
        raise HTTPException(status_code=403, detail="No access") from err

    return QuestOut.model_validate(quest, from_attributes=True)


@router.post("", response_model=QuestOut, summary="Create quest")
async def create_quest(
    payload: QuestCreate,
    workspace_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    preview: PreviewContext = Depends(get_preview_context),
):
    """Create a new quest owned by the current user."""
    if workspace_id is None:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    # Квота на создание историй (stories/month) по тарифу
    from app.domains.premium.quotas import check_and_consume_quota

    await check_and_consume_quota(
        db,
        current_user.id,
        quota_key="stories",
        amount=1,
        scope="month",
        preview=preview,
    )

    from app.domains.quests.authoring import create_quest as create_quest_domain

    quest = await create_quest_domain(
        db, payload=payload, author=current_user, workspace_id=workspace_id
    )
    await navcache.invalidate_compass_by_user(current_user.id)
    return quest


@router.put("/{quest_id}", response_model=QuestOut, summary="Update quest")
async def update_quest(
    quest_id: UUID,
    payload: QuestUpdate,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Modify quest fields if the user is the author."""
    from app.domains.quests.authoring import update_quest as update_quest_domain

    try:
        quest = await update_quest_domain(
            db,
            quest_id=quest_id,
            workspace_id=workspace_id,
            payload=payload,
            actor=current_user,
        )
    except ValueError as err:
        raise HTTPException(status_code=404, detail="Quest not found") from err
    except PermissionError as err:
        raise HTTPException(status_code=403, detail="Not authorized") from err
    await navcache.invalidate_compass_by_user(current_user.id)
    return quest


@router.post(
    "/{quest_id}/publish",
    response_model=QuestOut,
    summary="Publish quest",
)
async def publish_quest(
    quest_id: UUID,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a draft quest as published."""
    result = await db.execute(
        select(Quest).where(
            Quest.id == quest_id,
            Quest.workspace_id == workspace_id,
            Quest.is_deleted.is_(False),
        )
    )
    quest = result.scalars().first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    # Author or moderator can publish
    assert_owner_or_role(quest.author_id, "moderator", current_user)

    from app.domains.quests.versions import ValidationFailed, release_latest

    try:
        quest = await release_latest(
            db, quest_id=quest_id, workspace_id=workspace_id, actor=current_user
        )
    except ValidationFailed as err:
        raise HTTPException(
            status_code=400,
            detail={"code": "VALIDATION_FAILED", "report": getattr(err, "report", {})},
        ) from err
    await navcache.invalidate_compass_all()
    return quest


@router.delete("/{quest_id}", response_model=dict, summary="Delete quest")
async def delete_quest(
    quest_id: UUID,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a quest owned by the current user."""
    from app.domains.quests.authoring import delete_quest_soft

    try:
        await delete_quest_soft(
            db, quest_id=quest_id, workspace_id=workspace_id, actor=current_user
        )
    except ValueError as err:
        raise HTTPException(status_code=404, detail="Quest not found") from err
    except PermissionError as err:
        raise HTTPException(status_code=403, detail="Not authorized") from err
    await navcache.invalidate_compass_by_user(current_user.id)
    return {"status": "ok"}


@router.post(
    "/{quest_id}/start",
    response_model=QuestProgressOut,
    summary="Start quest",
)
async def start_quest(
    quest_id: UUID,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Begin or restart progress for a quest."""
    from app.domains.quests.gameplay import start_quest as start_quest_domain

    try:
        progress = await start_quest_domain(
            db, quest_id=quest_id, workspace_id=workspace_id, user=current_user
        )
    except ValueError as err:
        raise HTTPException(status_code=404, detail="Quest not found") from err
    except PermissionError as err:
        raise HTTPException(status_code=403, detail="No access") from err
    return progress


@router.get(
    "/{quest_id}/progress",
    response_model=QuestProgressOut,
    summary="Get progress",
)
async def get_progress(
    quest_id: UUID,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve progress of the current user in a quest."""
    from app.domains.quests.gameplay import get_progress as get_progress_domain

    try:
        progress = await get_progress_domain(
            db, quest_id=quest_id, workspace_id=workspace_id, user=current_user
        )
    except ValueError as err:
        raise HTTPException(status_code=404, detail="Progress not found") from err
    return progress


@router.get(
    "/{quest_id}/nodes/{node_id}",
    response_model=NodeOut,
    summary="Get quest node",
)
async def get_quest_node(
    quest_id: UUID,
    node_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return node details within a quest and update progress."""
    from app.domains.quests.gameplay import get_node as get_node_domain

    try:
        node = await get_node_domain(
            db, quest_id=quest_id, node_id=node_id, user=current_user
        )
    except ValueError as err:
        msg = str(err)
        if "Quest not found" in msg:
            raise HTTPException(status_code=404, detail="Quest not found") from err
        raise HTTPException(status_code=404, detail="Node not found") from err
    except PermissionError as err:
        raise HTTPException(status_code=403, detail="No access") from err
    return node


@router.post("/{quest_id}/buy", response_model=dict, summary="Buy quest")
async def buy_quest(
    quest_id: UUID,
    payload: QuestBuyIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Purchase access to a paid quest."""
    result = await db.execute(
        select(Quest).where(Quest.id == quest_id, Quest.is_deleted.is_(False))
    )
    quest = result.scalars().first()
    if not quest or quest.is_draft:
        raise HTTPException(status_code=404, detail="Quest not found")
    if quest.price in (None, 0):
        return {"status": "free"}
    res = await db.execute(
        select(QuestPurchase).where(
            QuestPurchase.quest_id == quest.id,
            QuestPurchase.user_id == current_user.id,
            QuestPurchase.workspace_id == quest.workspace_id,
        )
    )
    purchase = res.scalars().first()
    if purchase:
        return {"status": "already"}
    if not payload.payment_token:
        raise HTTPException(status_code=400, detail="Payment token required")
    # Валюта может храниться в самом квесте/настройках; используем "USD" по умолчанию
    from app.domains.payments.manager import verify_payment as verify_pay

    ok, gw = await verify_pay(
        db, amount=int(quest.price or 0), currency="USD", token=payload.payment_token
    )
    if not ok:
        raise HTTPException(status_code=400, detail="Payment not confirmed")

    # Фиксируем транзакцию с расчётом комиссии
    from app.domains.payments.ledger import capture_transaction

    breakdown = await capture_transaction(
        db,
        user_id=current_user.id,
        gateway_slug=gw,
        product_type="quest_purchase",
        product_id=quest.id,
        gross_cents=int(quest.price or 0),
        currency="USD",
        status="captured",
        extra_meta={"quest_slug": quest.slug},
    )

    purchase = QuestPurchase(
        quest_id=quest.id,
        user_id=current_user.id,
        workspace_id=quest.workspace_id,
    )
    db.add(purchase)
    await db.commit()
    return {"status": "ok", **breakdown}
