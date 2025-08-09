from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.security import verify_access_token
from app.db.session import get_db
from app.models.node import Node
from app.models.user import User
from app.models.transition import NodeTransition
from app.models.echo_trace import EchoTrace
from app.models.node_trace import NodeTrace
from app.api.auth import _authenticate

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
    return templates.TemplateResponse("admin/dashboard.html", {"request": request, "user": user})


@router.get("/nodes", response_class=HTMLResponse)
async def list_nodes(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    result = await db.execute(select(Node).order_by(Node.created_at.desc()).limit(100))
    nodes = result.scalars().all()
    return templates.TemplateResponse("admin/nodes.html", {"request": request, "nodes": nodes})


@router.get("/users", response_class=HTMLResponse)
async def list_users(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    result = await db.execute(select(User).order_by(User.created_at.desc()).limit(100))
    users = result.scalars().all()
    return templates.TemplateResponse("admin/users.html", {"request": request, "users": users})


@router.get("/transitions", response_class=HTMLResponse)
async def list_transitions(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    result = await db.execute(select(NodeTransition).order_by(NodeTransition.created_at.desc()).limit(100))
    transitions = result.scalars().all()
    return templates.TemplateResponse("admin/transitions.html", {"request": request, "transitions": transitions})


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
