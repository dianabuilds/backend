from pathlib import Path
from datetime import datetime
import json
from types import SimpleNamespace

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import load_only
from uuid import UUID as PyUUID

from app.core.config import settings
from app.core.security import verify_access_token
from app.db.session import get_db
from app.models.node import Node, ContentFormat
from app.models.user import User
from app.models.transition import NodeTransition, NodeTransitionType
from app.models.echo_trace import EchoTrace
from app.models.node_trace import NodeTrace
from app.models.achievement import Achievement
from app.models.quest import Quest
from app.models.event_quest import EventQuest, EventQuestRewardType
from app.api.auth import _authenticate
from app.services.tags import get_or_create_tags
from app.engine.embedding import update_node_embedding

router = APIRouter(prefix="/admin", tags=["admin-ui"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.globals.update(env=settings.ENVIRONMENT)

async def _get_admin_user(request: Request, db: AsyncSession) -> User | None:
    token = request.cookies.get("token")
    if not token:
        return None
    user_id = verify_access_token(token)
    if not user_id:
        return None
    user = await db.get(User, user_id)
    if not user or user.role != "admin":
        return None
    return user


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("admin/login.html", {"request": request})


@router.post("/login")
async def login_action(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    token = await _authenticate(db, username, password)
    response = RedirectResponse(url="/admin", status_code=303)
    response.set_cookie("token", token.access_token, httponly=True)
    return response


@router.get("/logout")
async def logout_action():
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("token")
    return response


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    stats = {
        "users_total": await db.scalar(select(func.count()).select_from(User)),
        "users_active": await db.scalar(
            select(func.count()).select_from(User).where(User.is_active == True)
        ),
        "users_banned": await db.scalar(
            select(func.count()).select_from(User).where(User.is_active == False)
        ),
        "nodes_total": await db.scalar(select(func.count()).select_from(Node)),
        "nodes_hidden": await db.scalar(
            select(func.count()).select_from(Node).where(Node.is_visible == False)
        ),
        "quests_total": await db.scalar(select(func.count()).select_from(Quest)),
        "event_active": await db.scalar(
            select(func.count()).select_from(EventQuest).where(EventQuest.is_active == True)
        ),
    }
    context = {"request": request, "user": user, "stats": stats}
    return templates.TemplateResponse("admin/dashboard.html", context)


@router.get("/nodes", response_class=HTMLResponse)
async def list_nodes(
    request: Request,
    q: str | None = None,
    page: int = 1,
    db: AsyncSession = Depends(get_db),
):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)

    limit = 50
    stmt = select(Node).options(load_only(Node.id, Node.slug, Node.title)).order_by(
        Node.created_at.desc()
    )
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Node.title.ilike(like), Node.slug.ilike(like)))

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    result = await db.execute(stmt.offset((page - 1) * limit).limit(limit))
    nodes = result.scalars().all()

    context = {
        "request": request,
        "nodes": nodes,
        "page": page,
        "q": q or "",
        "has_prev": page > 1,
        "has_next": total > page * limit,
    }
    return templates.TemplateResponse("admin/nodes.html", context)


@router.get("/nodes/new", response_class=HTMLResponse)
async def new_node_form(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    return templates.TemplateResponse(
        "admin/node_form.html",
        {"request": request, "node": None, "formats": [f.value for f in ContentFormat]},
    )


@router.post("/nodes/new")
async def create_node_action(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    form = await request.form()
    title = form.get("title") or None
    content_format = ContentFormat(form.get("content_format"))
    content = form.get("content")
    tags_raw = form.get("tags") or ""
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    is_public = form.get("is_public") == "on"
    is_visible = form.get("is_visible") == "on"
    allow_feedback = form.get("allow_feedback") == "on"
    is_recommendable = form.get("is_recommendable") == "on"
    premium_only = form.get("premium_only") == "on"

    node = Node(
        title=title,
        content_format=content_format,
        content=content,
        media=[],
        is_public=is_public,
        is_visible=is_visible,
        allow_feedback=allow_feedback,
        is_recommendable=is_recommendable,
        premium_only=premium_only,
        author_id=user.id,
    )
    if tags:
        node.tags = await get_or_create_tags(db, tags)
    db.add(node)
    await db.commit()
    await db.refresh(node)
    await update_node_embedding(db, node)
    return RedirectResponse(url="/admin/nodes", status_code=303)


@router.get("/nodes/{node_id}/edit", response_class=HTMLResponse)
async def edit_node_form(node_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    node = await db.get(Node, node_id)
    if not node:
        return RedirectResponse(url="/admin/nodes", status_code=303)
    await db.refresh(node, attribute_names=["tags"])
    return templates.TemplateResponse(
        "admin/node_form.html",
        {
            "request": request,
            "node": node,
            "formats": [f.value for f in ContentFormat],
        },
    )


@router.post("/nodes/{node_id}/edit")
async def update_node_action(node_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    node = await db.get(Node, node_id)
    if not node:
        return RedirectResponse(url="/admin/nodes", status_code=303)
    form = await request.form()
    node.title = form.get("title") or None
    node.content_format = ContentFormat(form.get("content_format"))
    node.content = form.get("content")
    tags_raw = form.get("tags") or ""
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    node.is_public = form.get("is_public") == "on"
    node.is_visible = form.get("is_visible") == "on"
    node.allow_feedback = form.get("allow_feedback") == "on"
    node.is_recommendable = form.get("is_recommendable") == "on"
    node.premium_only = form.get("premium_only") == "on"
    await db.refresh(node, attribute_names=["tags"])
    node.tags = await get_or_create_tags(db, tags) if tags else []
    node.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(node)
    await update_node_embedding(db, node)
    return RedirectResponse(url="/admin/nodes", status_code=303)


@router.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    q: str | None = None,
    page: int = 1,
    db: AsyncSession = Depends(get_db),
):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)

    limit = 50
    stmt = select(User).order_by(User.created_at.desc())
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(User.email.ilike(like), User.username.ilike(like)))

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    result = await db.execute(stmt.offset((page - 1) * limit).limit(limit))
    users = result.scalars().all()

    context = {
        "request": request,
        "users": users,
        "page": page,
        "q": q or "",
        "has_prev": page > 1,
        "has_next": total > page * limit,
    }
    return templates.TemplateResponse("admin/users.html", context)


@router.get("/transitions", response_class=HTMLResponse)
async def list_transitions(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    result = await db.execute(select(NodeTransition).order_by(NodeTransition.created_at.desc()).limit(100))
    transitions = result.scalars().all()
    return templates.TemplateResponse("admin/transitions.html", {"request": request, "transitions": transitions})


@router.get("/transitions/new", response_class=HTMLResponse)
async def new_transition_form(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    result = await db.execute(select(Node).order_by(Node.created_at.desc()).limit(100))
    nodes = result.scalars().all()
    return templates.TemplateResponse(
        "admin/transition_form.html",
        {
            "request": request,
            "nodes": nodes,
            "types": [t.value for t in NodeTransitionType],
        },
    )


@router.post("/transitions/new")
async def create_transition_action(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    form = await request.form()
    from_id = form.get("from_node")
    to_id = form.get("to_node")
    type_val = form.get("type") or NodeTransitionType.manual.value
    weight = int(form.get("weight") or 1)
    label = form.get("label") or None
    from_node = await db.get(Node, from_id)
    to_node = await db.get(Node, to_id)
    if not from_node or not to_node:
        return RedirectResponse(url="/admin/transitions/new", status_code=303)
    transition = NodeTransition(
        from_node_id=from_node.id,
        to_node_id=to_node.id,
        type=NodeTransitionType(type_val),
        weight=weight,
        label=label,
        created_by=user.id,
    )
    db.add(transition)
    await db.commit()
    return RedirectResponse(url="/admin/transitions", status_code=303)


@router.get("/event-quests", response_class=HTMLResponse)
async def list_event_quests(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    result = await db.execute(select(EventQuest).order_by(EventQuest.starts_at.desc()))
    quests = result.scalars().all()
    return templates.TemplateResponse(
        "admin/event_quests.html", {"request": request, "quests": quests}
    )


@router.get("/event-quests/new", response_class=HTMLResponse)
async def new_event_quest_form(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    result = await db.execute(select(Node).order_by(Node.created_at.desc()).limit(100))
    nodes = result.scalars().all()
    return templates.TemplateResponse(
        "admin/event_quest_form.html",
        {
            "request": request,
            "quest": None,
            "nodes": nodes,
            "reward_types": [r.value for r in EventQuestRewardType],
        },
    )


@router.post("/event-quests/new")
async def create_event_quest_action(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    form = await request.form()
    hints_tags = [t.strip() for t in (form.get("hints_tags") or "").split(",") if t.strip()]
    hints_keywords = [t.strip() for t in (form.get("hints_keywords") or "").split(",") if t.strip()]
    traces_raw = [t.strip() for t in (form.get("hints_trace") or "").split(",") if t.strip()]
    hints_trace = []
    for tr in traces_raw:
        try:
            hints_trace.append(PyUUID(tr))
        except Exception:
            continue
    quest = EventQuest(
        title=form.get("title") or "",
        target_node_id=form.get("target_node"),
        hints_tags=hints_tags,
        hints_keywords=hints_keywords,
        hints_trace=hints_trace,
        starts_at=datetime.fromisoformat(form.get("starts_at")),
        expires_at=datetime.fromisoformat(form.get("expires_at")),
        max_rewards=int(form.get("max_rewards") or 0),
        reward_type=EventQuestRewardType(form.get("reward_type")),
        is_active=form.get("is_active") == "on",
    )
    db.add(quest)
    await db.commit()
    return RedirectResponse(url="/admin/event-quests", status_code=303)


@router.get("/event-quests/{quest_id}/edit", response_class=HTMLResponse)
async def edit_event_quest_form(quest_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    quest = await db.get(EventQuest, quest_id)
    if not quest:
        return RedirectResponse(url="/admin/event-quests", status_code=303)
    result = await db.execute(select(Node).order_by(Node.created_at.desc()).limit(100))
    nodes = result.scalars().all()
    return templates.TemplateResponse(
        "admin/event_quest_form.html",
        {
            "request": request,
            "quest": quest,
            "nodes": nodes,
            "reward_types": [r.value for r in EventQuestRewardType],
        },
    )


@router.post("/event-quests/{quest_id}/edit")
async def update_event_quest_action(quest_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    quest = await db.get(EventQuest, quest_id)
    if not quest:
        return RedirectResponse(url="/admin/event-quests", status_code=303)
    form = await request.form()
    quest.title = form.get("title") or ""
    quest.target_node_id = form.get("target_node")
    quest.hints_tags = [t.strip() for t in (form.get("hints_tags") or "").split(",") if t.strip()]
    quest.hints_keywords = [t.strip() for t in (form.get("hints_keywords") or "").split(",") if t.strip()]
    traces_raw = [t.strip() for t in (form.get("hints_trace") or "").split(",") if t.strip()]
    quest.hints_trace = []
    for tr in traces_raw:
        try:
            quest.hints_trace.append(PyUUID(tr))
        except Exception:
            continue
    quest.starts_at = datetime.fromisoformat(form.get("starts_at"))
    quest.expires_at = datetime.fromisoformat(form.get("expires_at"))
    quest.max_rewards = int(form.get("max_rewards") or 0)
    quest.reward_type = EventQuestRewardType(form.get("reward_type"))
    quest.is_active = form.get("is_active") == "on"
    await db.commit()
    return RedirectResponse(url="/admin/event-quests", status_code=303)


@router.get("/echoes", response_class=HTMLResponse)
async def list_echoes(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    result = await db.execute(select(EchoTrace).order_by(EchoTrace.created_at.desc()).limit(100))
    echoes = result.scalars().all()
    return templates.TemplateResponse("admin/echoes.html", {"request": request, "echoes": echoes})


@router.get("/traces", response_class=HTMLResponse)
async def list_traces(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    result = await db.execute(select(NodeTrace).order_by(NodeTrace.created_at.desc()).limit(100))
    traces = result.scalars().all()
    return templates.TemplateResponse("admin/traces.html", {"request": request, "traces": traces})


@router.get("/premium", response_class=HTMLResponse)
async def premium_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    result = await db.execute(select(User).where(User.is_premium == True).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return templates.TemplateResponse("admin/premium.html", {"request": request, "users": users})


@router.post("/premium")
async def set_premium(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    form = await request.form()
    target_id = form.get("user_id")
    until = form.get("premium_until")
    target = await db.get(User, target_id)
    if not target:
        return RedirectResponse(url="/admin/premium", status_code=303)
    target.is_premium = True
    target.premium_until = datetime.fromisoformat(until) if until else None
    await db.commit()
    return RedirectResponse(url="/admin/premium", status_code=303)
# Achievements admin
@router.get('/achievements', response_class=HTMLResponse)
async def list_achievements(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url='/admin/login', status_code=303)
    result = await db.execute(select(Achievement).order_by(Achievement.code))
    achievements = result.scalars().all()
    return templates.TemplateResponse(
        'admin/achievements.html',
        {'request': request, 'achievements': achievements},
    )

ALLOWED_CONDITION_TYPES = {
    'event_count',
    'tag_interaction',
    'premium_status',
    'first_action',
    'quest_complete',
    'nodes_created',
    'views_count',
}

def _parse_condition(condition_str: str):
    try:
        data = json.loads(condition_str)
    except Exception:
        return None, 'Invalid JSON condition'
    if data.get('type') not in ALLOWED_CONDITION_TYPES:
        return None, 'Unknown condition type'
    return data, None

@router.get('/achievements/new', response_class=HTMLResponse)
async def new_achievement_form(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url='/admin/login', status_code=303)
    return templates.TemplateResponse(
        'admin/achievement_form.html',
        {'request': request, 'achievement': None, 'condition': '{}', 'error': None},
    )

@router.post('/achievements/new')
async def create_achievement_action(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url='/admin/login', status_code=303)
    form = await request.form()
    code = form.get('code')
    title = form.get('title')
    description = form.get('description') or None
    icon = form.get('icon') or None
    condition_str = form.get('condition') or '{}'
    visible = form.get('visible') == 'on'

    condition, error = _parse_condition(condition_str)
    if not code:
        error = 'Code is required'
    else:
        result = await db.execute(select(Achievement).where(Achievement.code == code))
        if result.scalars().first():
            error = 'Code must be unique'
    if error:
        temp = SimpleNamespace(
            code=code,
            title=title,
            description=description,
            icon=icon,
            visible=visible,
        )
        return templates.TemplateResponse(
            'admin/achievement_form.html',
            {
                'request': request,
                'achievement': temp,
                'condition': condition_str,
                'error': error,
            },
        )

    ach = Achievement(
        code=code,
        title=title,
        description=description,
        icon=icon,
        condition=condition,
        visible=visible,
    )
    db.add(ach)
    await db.commit()
    return RedirectResponse(url='/admin/achievements', status_code=303)

@router.get('/achievements/{achievement_id}/edit', response_class=HTMLResponse)
async def edit_achievement_form(achievement_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url='/admin/login', status_code=303)
    achievement = await db.get(Achievement, achievement_id)
    if not achievement:
        return RedirectResponse(url='/admin/achievements', status_code=303)
    condition_str = json.dumps(achievement.condition, indent=2)
    return templates.TemplateResponse(
        'admin/achievement_form.html',
        {
            'request': request,
            'achievement': achievement,
            'condition': condition_str,
            'error': None,
        },
    )

@router.post('/achievements/{achievement_id}/edit')
async def update_achievement_action(achievement_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url='/admin/login', status_code=303)
    achievement = await db.get(Achievement, achievement_id)
    if not achievement:
        return RedirectResponse(url='/admin/achievements', status_code=303)
    form = await request.form()
    code = form.get('code')
    title = form.get('title')
    description = form.get('description') or None
    icon = form.get('icon') or None
    condition_str = form.get('condition') or '{}'
    visible = form.get('visible') == 'on'

    condition, error = _parse_condition(condition_str)
    if not code:
        error = 'Code is required'
    else:
        result = await db.execute(
            select(Achievement).where(
                Achievement.code == code, Achievement.id != achievement.id
            )
        )
        if result.scalars().first():
            error = 'Code must be unique'
    if error:
        temp = SimpleNamespace(
            code=code,
            title=title,
            description=description,
            icon=icon,
            visible=visible,
        )
        return templates.TemplateResponse(
            'admin/achievement_form.html',
            {
                'request': request,
                'achievement': temp,
                'condition': condition_str,
                'error': error,
            },
        )

    achievement.code = code
    achievement.title = title
    achievement.description = description
    achievement.icon = icon
    achievement.condition = condition
    achievement.visible = visible
    await db.commit()
    return RedirectResponse(url='/admin/achievements', status_code=303)
