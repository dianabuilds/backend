from __future__ import annotations

from datetime import datetime

# Этот модуль ранее пытался переимпортировать несуществующий legacy-роутер,
# из-за чего импорт падал и все админские эндпоинты для AI-квестов возвращали
# 404.  Удаляем лишний импорт и используем собственный роутер ниже.
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import admin_required, get_preview_context
from app.core.preview import PreviewContext
from app.domains.ai.infrastructure.models.ai_settings import AISettings
from app.domains.ai.infrastructure.models.generation_models import (
    GenerationJob,
    JobStatus,
)
from app.domains.ai.infrastructure.models.world_models import Character
from app.domains.ai.infrastructure.models.world_models import WorldTemplate as World
from app.domains.ai.schemas.ai_quests import (
    GenerateQuestIn,
    GenerationEnqueued,
    GenerationJobOut,
    TickIn,
)
from app.domains.ai.schemas.worlds import (
    CharacterIn,
    CharacterOut,
    WorldTemplateIn,
    WorldTemplateOut,
)
from app.domains.ai.services.generation import enqueue_generation_job
from app.domains.quests.infrastructure.models.quest_models import Quest
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required_dep = require_admin_role({"admin", "moderator"})
CurrentUser = Annotated[User, Depends(admin_required)]

router = APIRouter(
    prefix="/admin/ai/quests",
    tags=["admin", "admin-ai-quests"],
    responses=ADMIN_AUTH_RESPONSES,
    dependencies=[Depends(admin_required_dep)],
)


@router.get("/templates", summary="List world templates")
async def list_world_templates(
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    _: Annotated[Depends, Depends(admin_required)] = ...,
) -> list[dict[str, Any]]:
    res = await db.execute(select(World).order_by(World.title.asc()))
    worlds = list(res.scalars().all())
    return [{"id": str(w.id), "title": w.title, "locale": w.locale} for w in worlds]


@router.post(
    "/generate",
    response_model=GenerationEnqueued,
    summary="Enqueue AI quest generation",
)
async def generate_ai_quest(
    body: GenerateQuestIn,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current: CurrentUser = ...,
    reuse: bool = True,
    preview: Annotated[PreviewContext, Depends(get_preview_context)] = ...,
) -> GenerationEnqueued:
    params = {
        "world_template_id": (str(body.world_template_id) if body.world_template_id else None),
        "structure": body.structure,
        "length": body.length,
        "tone": body.tone,
        "genre": body.genre,
        "locale": body.locale,
        "extras": body.extras or {},
    }
    # Настройки провайдера/модели
    res = await db.execute(select(AISettings).limit(1))
    settings = res.scalar_one_or_none()
    provider = settings.provider if settings and settings.provider else None
    model = body.model or (settings.model if settings and settings.model else None)

    job = await enqueue_generation_job(
        db,
        created_by=getattr(current, "id", None),
        params=params,
        provider=provider,
        model=model,
        reuse=reuse,
        preview=preview,
    )
    if body.remember and getattr(current, "id", None) and body.model:
        from app.domains.ai.infrastructure.repositories.user_pref_repository import (
            UserAIPrefRepository,
        )

        repo = UserAIPrefRepository(db)
        await repo.set(current.id, body.model)
    await db.commit()
    return GenerationEnqueued(job_id=job.id)


@router.get("/jobs", response_model=list[GenerationJobOut], summary="List AI generation jobs")
async def list_jobs(
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    _: Annotated[Depends, Depends(admin_required)] = ...,
) -> list[GenerationJobOut]:
    res = await db.execute(select(GenerationJob).order_by(GenerationJob.created_at.desc()))
    rows = list(res.scalars().all())
    return [GenerationJobOut.model_validate(r) for r in rows]


@router.get("/jobs/{job_id}", response_model=GenerationJobOut, summary="Get job by id")
async def get_job(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    _: Annotated[Depends, Depends(admin_required)] = ...,
) -> GenerationJobOut:
    job = await db.get(GenerationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return GenerationJobOut.model_validate(job)


@router.post(
    "/jobs/{job_id}/simulate_complete",
    response_model=GenerationJobOut,
    summary="Simulate job completion (DEV)",
)
async def simulate_complete(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current: Annotated[User, Depends(admin_required)] = ...,
) -> GenerationJobOut:
    job = await db.get(GenerationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    now = datetime.utcnow()
    if job.status == JobStatus.queued:
        job.status = JobStatus.running
        job.started_at = now

    # Создадим черновой квест при необходимости
    if not job.result_quest_id:
        title = (
            f"AI Quest ({job.params.get('structure','?')}/"
            f"{job.params.get('length','?')}/"
            f"{job.params.get('tone','?')})"
        )
        q = Quest(
            title=title,
            subtitle=None,
            description=f"Generated by AI ({job.params.get('genre','genre')})",
            author_id=current.id,
            is_draft=True,
            structure=job.params.get("structure"),
            length=job.params.get("length"),
            tone=job.params.get("tone"),
            genre=job.params.get("genre"),
            locale=job.params.get("locale"),
        )
        db.add(q)
        await db.flush()
        job.result_quest_id = q.id

    # Стоимость/токены (заглушка)
    job.cost = job.cost or 0.0123
    job.token_usage = job.token_usage or {
        "prompt_tokens": 1024,
        "completion_tokens": 4096,
    }
    # Сохраним стоимость в квест
    q = await db.get(Quest, job.result_quest_id) if job.result_quest_id else None
    if q:
        try:
            q.cost_generation = int(round(float(job.cost or 0) * 100))
        except Exception:
            q.cost_generation = None
        q.structure = q.structure or job.params.get("structure")
        q.length = q.length or job.params.get("length")
        q.tone = q.tone or job.params.get("tone")
        q.genre = q.genre or job.params.get("genre")
        q.locale = q.locale or job.params.get("locale")

    # Прогресс и лог
    job.progress = 100
    logs = list(job.logs or [])
    logs.append(f"[{datetime.utcnow().isoformat()}] Job completed")
    job.logs = logs

    job.status = JobStatus.completed
    job.finished_at = datetime.utcnow()

    await db.commit()
    await db.refresh(job)
    return GenerationJobOut.model_validate(job)


@router.post(
    "/jobs/{job_id}/tick",
    response_model=GenerationJobOut,
    summary="Advance job progress (DEV)",
)
async def tick_job(
    job_id: UUID,
    body: dict | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current: Annotated[User, Depends(admin_required)] = ...,
) -> GenerationJobOut:
    job = await db.get(GenerationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    payload = TickIn(**(body or {}))
    now = datetime.utcnow()
    if job.status == JobStatus.queued:
        job.status = JobStatus.running
        job.started_at = now
    if job.status == JobStatus.running:
        job.progress = max(0, min(100, int((job.progress or 0) + payload.delta)))
        if job.progress >= 100:
            job.status = JobStatus.completed
            job.finished_at = datetime.utcnow()

    logs = list(job.logs or [])
    logs.append(
        f"[{datetime.utcnow().isoformat()}] Tick {payload.delta}%"
        f"{(' - ' + payload.message) if payload.message else ''}"
    )
    job.logs = logs

    await db.commit()
    await db.refresh(job)
    return GenerationJobOut.model_validate(job)


# -------- Worlds & Characters CRUD --------


@router.get("/worlds", response_model=list[WorldTemplateOut], summary="List worlds")
async def list_worlds(
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    _: Annotated[Depends, Depends(admin_required)] = ...,
) -> list[WorldTemplateOut]:
    res = await db.execute(select(World).order_by(World.title.asc()))
    rows = list(res.scalars().all())
    return [WorldTemplateOut.model_validate(r) for r in rows]


@router.post("/worlds", response_model=WorldTemplateOut, summary="Create world")
async def create_world(
    body: WorldTemplateIn,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current: Annotated[User, Depends(admin_required)] = ...,
) -> WorldTemplateOut:
    w = World(
        id=uuid4(),
        title=body.title,
        locale=body.locale,
        description=body.description,
        meta=body.meta,
        created_by_user_id=current.id,
    )
    db.add(w)
    await db.commit()
    await db.refresh(w)
    return WorldTemplateOut.model_validate(w)


@router.put("/worlds/{world_id}", response_model=WorldTemplateOut, summary="Update world")
async def update_world(
    world_id: UUID,
    body: WorldTemplateIn,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current: Annotated[User, Depends(admin_required)] = ...,
) -> WorldTemplateOut:
    w = await db.get(World, world_id)
    if not w:
        raise HTTPException(status_code=404, detail="World not found")
    if body.title is not None:
        w.title = body.title
    w.locale = body.locale
    w.description = body.description
    w.meta = body.meta
    w.updated_by_user_id = current.id
    await db.commit()
    await db.refresh(w)
    return WorldTemplateOut.model_validate(w)


@router.delete("/worlds/{world_id}", summary="Delete world")
async def delete_world(
    world_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current: Annotated[User, Depends(admin_required)] = ...,
) -> dict:
    w = await db.get(World, world_id)
    if not w:
        raise HTTPException(status_code=404, detail="World not found")
    await db.delete(w)
    await db.commit()
    return {"ok": True}


@router.get(
    "/worlds/{world_id}/characters",
    response_model=list[CharacterOut],
    summary="List characters for world",
)
async def list_characters(
    world_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    _: Annotated[Depends, Depends(admin_required)] = ...,
) -> list[CharacterOut]:
    res = await db.execute(
        select(Character).where(Character.world_id == world_id).order_by(Character.name.asc())
    )
    rows = list(res.scalars().all())
    return [CharacterOut.model_validate(r) for r in rows]


@router.post(
    "/worlds/{world_id}/characters",
    response_model=CharacterOut,
    summary="Create character",
)
async def create_character(
    world_id: UUID,
    body: CharacterIn,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current: Annotated[User, Depends(admin_required)] = ...,
) -> CharacterOut:
    w = await db.get(World, world_id)
    if not w:
        raise HTTPException(status_code=404, detail="World not found")
    c = Character(
        id=uuid4(),
        world_id=world_id,
        name=body.name,
        role=body.role,
        description=body.description,
        traits=body.traits,
        created_by_user_id=current.id,
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return CharacterOut.model_validate(c)


@router.put(
    "/characters/{character_id}",
    response_model=CharacterOut,
    summary="Update character",
)
async def update_character(
    character_id: UUID,
    body: CharacterIn,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current: Annotated[User, Depends(admin_required)] = ...,
) -> CharacterOut:
    c = await db.get(Character, character_id)
    if not c:
        raise HTTPException(status_code=404, detail="Character not found")
    if body.name is not None:
        c.name = body.name
    c.role = body.role
    c.description = body.description
    c.traits = body.traits
    c.updated_by_user_id = current.id
    await db.commit()
    await db.refresh(c)
    return CharacterOut.model_validate(c)


@router.delete("/characters/{character_id}", summary="Delete character")
async def delete_character(
    character_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current: Annotated[User, Depends(admin_required)] = ...,
) -> dict:
    c = await db.get(Character, character_id)
    if not c:
        raise HTTPException(status_code=404, detail="Character not found")
    await db.delete(c)
    await db.commit()
    return {"ok": True}
