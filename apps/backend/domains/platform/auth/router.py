from __future__ import annotations

import hashlib
import logging

logging.basicConfig(level=logging.INFO)
import os
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def _normalize_db_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        try:
            import psycopg  # type: ignore  # noqa: F401

            return "postgresql+psycopg" + url[len("postgresql+asyncpg") :]
        except Exception:
            try:
                import psycopg2  # type: ignore  # noqa: F401

                return "postgresql+psycopg2" + url[len("postgresql+asyncpg") :]
            except Exception:
                return "postgresql" + url[len("postgresql+asyncpg") :]
    return url


def get_engine() -> Engine:
    url = os.getenv("APP_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("Database URL not set in APP_DATABASE_URL/DATABASE_URL")
    url = _normalize_db_url(url)
    return create_engine(url, future=True, pool_pre_ping=True)


ENGINE = get_engine()


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _session_settings() -> dict:
    session_hours = int(os.getenv("SESSION_HOURS", "12"))
    refresh_days = int(os.getenv("REFRESH_DAYS", "30"))
    secure = os.getenv("COOKIE_SECURE", "1") in {"1", "true", "True"}
    samesite = os.getenv("COOKIE_SAMESITE", "lax").lower()
    domain = os.getenv("COOKIE_DOMAIN")
    return {
        "session_hours": session_hours,
        "refresh_days": refresh_days,
        "secure": secure,
        "samesite": (
            "strict" if samesite == "strict" else ("none" if samesite == "none" else "lax")
        ),
        "domain": domain,
    }


class RegisterIn(BaseModel):
    username: str
    password: str
    email: EmailStr | None = None
    display_name: str | None = None


class LoginIn(BaseModel):
    login: str  # username or email
    password: str


class MeOut(BaseModel):
    id: str
    username: str
    email: str | None = None
    display_name: str | None = None
    is_active: bool
    roles: list[str] = []


def _set_cookies(resp: Response, session_token: str, refresh_token: str | None) -> None:
    cfg = _session_settings()
    resp.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        secure=cfg["secure"],
        samesite=cfg["samesite"],
        max_age=cfg["session_hours"] * 3600,
        domain=cfg["domain"],
        path="/",
    )
    if refresh_token:
        resp.set_cookie(
            key="refresh",
            value=refresh_token,
            httponly=True,
            secure=cfg["secure"],
            samesite=cfg["samesite"],
            max_age=cfg["refresh_days"] * 86400,
            domain=cfg["domain"],
            path="/",
        )


def _clear_cookies(resp: Response) -> None:
    cfg = _session_settings()
    for name in ("session", "refresh"):
        resp.delete_cookie(key=name, domain=cfg["domain"], path="/")


def _require_session(request: Request):
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    token_hash = _hash(token)
    with ENGINE.begin() as conn:
        row = (
            conn.execute(
                text(
                    """
                SELECT u.id, u.username, u.email, u.display_name, u.is_active,
                       COALESCE(array_agg(r.role) FILTER (WHERE r.role IS NOT NULL), ARRAY[]::user_role[]) AS roles
                FROM user_sessions s
                JOIN users u ON u.id = s.user_id
                LEFT JOIN user_roles r ON r.user_id = u.id
                WHERE s.session_token_hash = :h
                  AND s.revoked_at IS NULL
                  AND now() < s.expires_at
                GROUP BY u.id, u.username, u.email, u.display_name, u.is_active
                """
                ),
                {"h": token_hash},
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return row


@router.post("/register", response_model=MeOut)
def register(data: RegisterIn, response: Response):
    if len(data.username) < 3 or len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Invalid username or password length")
    with ENGINE.begin() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM users WHERE lower(username)=lower(:u)"),
            {"u": data.username},
        ).first()
        if exists:
            raise HTTPException(status_code=409, detail="Username already taken")

        user = (
            conn.execute(
                text(
                    """
                INSERT INTO users (username, email, display_name, is_active, password_hash)
                VALUES (:u, :e, :d, TRUE, crypt(:p, gen_salt('bf')))
                        RETURNING id, username, email, display_name, is_active
                """
                ),
                {
                    "u": data.username,
                    "e": data.email,
                    "d": data.display_name,
                    "p": data.password,
                },
            )
            .mappings()
            .first()
        )
        # grant default role 'user'
        conn.execute(
            text(
                "INSERT INTO user_roles (user_id, role) VALUES (:uid, 'user') ON CONFLICT DO NOTHING"
            ),
            {"uid": user["id"]},
        )

        cfg = _session_settings()
        session_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        conn.execute(
            text(
                """
                INSERT INTO user_sessions (user_id, session_token_hash, refresh_token_hash, expires_at, refresh_expires_at)
                VALUES (:uid, :sh, :rh, now() + (:shours || ' hours')::interval, now() + (:rdays || ' days')::interval)
                """
            ),
            {
                "uid": user["id"],
                "sh": _hash(session_token),
                "rh": _hash(refresh_token),
                "shours": cfg["session_hours"],
                "rdays": cfg["refresh_days"],
            },
        )
    _set_cookies(response, session_token, refresh_token)
    return {**user, "roles": ["user"]}


@router.post("/login", response_model=MeOut)
def login(data: LoginIn, request: Request, response: Response):
    print("Auth login attempt for", data.login, flush=True)
    with ENGINE.begin() as conn:
        row = (
            conn.execute(
                text(
                    """
                SELECT u.id, u.username, u.email, u.display_name, u.is_active,
                       COALESCE(array_agg(r.role) FILTER (WHERE r.role IS NOT NULL), ARRAY[]::user_role[]) AS roles
                FROM users u
                LEFT JOIN user_roles r ON r.user_id = u.id
                WHERE (lower(u.username)=lower(:l) OR lower(u.email)=lower(:l))
                  AND u.password_hash = crypt(:p, u.password_hash)
                GROUP BY u.id, u.username, u.email, u.display_name, u.is_active
                """
                ),
                {"l": data.login, "p": data.password},
            )
            .mappings()
            .first()
        )
        if row:
            print("Auth login success for", data.login, "id", row["id"], flush=True)
        else:
            print(
                "Auth login failed for",
                data.login,
                "(no matching credentials)",
                flush=True,
            )
        if not row:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        cfg = _session_settings()
        ua = request.headers.get("user-agent")
        ip = request.client.host if request.client else None
        session_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        conn.execute(
            text(
                """
                INSERT INTO user_sessions (user_id, session_token_hash, refresh_token_hash, user_agent, ip, expires_at, refresh_expires_at)
                VALUES (:uid, :sh, :rh, :ua, :ip, now() + (:shours || ' hours')::interval, now() + (:rdays || ' days')::interval)
                """
            ),
            {
                "uid": row["id"],
                "sh": _hash(session_token),
                "rh": _hash(refresh_token),
                "ua": ua,
                "ip": ip,
                "shours": cfg["session_hours"],
                "rdays": cfg["refresh_days"],
            },
        )
    _set_cookies(response, session_token, refresh_token)
    return row


@router.post("/refresh", response_model=MeOut)
def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    refresh_hash = _hash(refresh_token)
    with ENGINE.begin() as conn:
        row = (
            conn.execute(
                text(
                    """
                SELECT s.user_id as id, u.username, u.email, u.display_name, u.is_active,
                       COALESCE(array_agg(r.role) FILTER (WHERE r.role IS NOT NULL), ARRAY[]::user_role[]) AS roles
                FROM user_sessions s
                JOIN users u ON u.id = s.user_id
                LEFT JOIN user_roles r ON r.user_id = u.id
                WHERE s.refresh_token_hash = :h
                  AND s.revoked_at IS NULL
                  AND now() < s.refresh_expires_at
                GROUP BY s.user_id, u.username, u.email, u.display_name, u.is_active
                """
                ),
                {"h": refresh_hash},
            )
            .mappings()
            .first()
        )
        if not row:
            raise HTTPException(status_code=401, detail="Invalid refresh")

        cfg = _session_settings()
        session_token = secrets.token_urlsafe(32)
        conn.execute(
            text(
                """
                UPDATE user_sessions
                SET session_token_hash = :sh,
                    expires_at = now() + (:shours || ' hours')::interval,
                    last_used_at = now()
                WHERE refresh_token_hash = :rh
                """
            ),
            {
                "sh": _hash(session_token),
                "shours": cfg["session_hours"],
                "rh": refresh_hash,
            },
        )
    _set_cookies(response, session_token, refresh_token)
    return row


@router.post("/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get("session")
    if token:
        with ENGINE.begin() as conn:
            conn.execute(
                text("UPDATE user_sessions SET revoked_at = now() WHERE session_token_hash = :h"),
                {"h": _hash(token)},
            )
    _clear_cookies(response)
    return {"ok": True}


@router.get("/me", response_model=MeOut)
def me(user=Depends(_require_session)):
    return user


def require_roles(*required: str):
    def dep(user=Depends(_require_session)):
        roles = set(user.get("roles") or [])
        if not roles.intersection(required):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return dep


@router.get("/admin/ping", dependencies=[Depends(require_roles("admin"))])
def admin_ping():
    return {"ok": True}
