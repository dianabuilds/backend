import uuid
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta

from eth_account.messages import encode_defunct
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from web3.auto import w3

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.models.user_token import UserToken, TokenAction
from app.services.mail import mail_service
from app.schemas.auth import (
    ChangePassword,
    EVMVerify,
    LoginSchema,
    SignupSchema,
    Token,
)
from app.core.log_events import auth_success, auth_failure
from app.core.log_filters import user_id_var
from app.core.rate_limit import rate_limit_dep

router = APIRouter(prefix="/auth", tags=["auth"])

# simple in-memory nonce store
nonce_store: dict[str, str] = {}


import logging

logger = logging.getLogger(__name__)

@router.post(
    "/signup",
    summary="Register new user",
    dependencies=[rate_limit_dep(settings.rate_limit.rules_signup)],
)
async def signup(payload: SignupSchema, db: AsyncSession = Depends(get_db)):
    """Create a new user account and send a verification email."""
    logger.info(f"Signup attempt for email: {payload.email} with username: {payload.username}")

    # Проверка на пустые значения
    if not payload.email or not payload.password or not payload.username:
        logger.warning("Signup attempt with empty email, username or password")
        auth_failure("missing_fields")
        raise HTTPException(status_code=400, detail="Email, username and password are required")

    # Проверка на существующий email
    email_result = await db.execute(select(User).where(User.email == payload.email))
    if email_result.scalars().first():
        logger.warning(f"Signup attempt with existing email: {payload.email}")
        auth_failure("duplicate_email")
        raise HTTPException(status_code=400, detail="Email already registered")

    # Проверка на существующий username
    username_result = await db.execute(select(User).where(User.username == payload.username))
    if username_result.scalars().first():
        logger.warning(f"Signup attempt with existing username: {payload.username}")
        auth_failure("duplicate_username")
        raise HTTPException(status_code=400, detail="Username already taken")

    try:
        # Создаем хэш пароля
        password_hash = get_password_hash(payload.password)

        # Создаем пользователя
        user = User(
            email=payload.email,
            username=payload.username,
            password_hash=password_hash,
        )

        # Добавляем в сессию и сохраняем
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Создаем токен подтверждения email
        raw_token = secrets.token_urlsafe(32)
        token_hash = hmac.new(
            settings.jwt.secret.encode(), raw_token.encode(), hashlib.sha256
        ).hexdigest()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        db.add(
            UserToken(
                user_id=user.id,
                action=TokenAction.verify,
                token_hash=token_hash,
                expires_at=expires_at,
            )
        )
        await db.commit()

        verify_link = f"/auth/verify?token={raw_token}"
        try:
            await mail_service.send_email(
                to=user.email,
                subject="Подтверждение e‑mail",
                template="auth/verify_email",
                context={
                    "username": user.username,
                    "verify_url": verify_link,
                },
            )
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")

        logger.info(f"User created successfully: {user.id}")
        user_id_var.set(str(user.id))
        auth_success(str(user.id))
        resp = {"message": "Verification email sent"}
        if not settings.is_production:
            resp["verification_token"] = raw_token
        return resp
    except Exception as e:
        await db.rollback()
        error_msg = str(e)
        logger.error(f"Error during user creation: {error_msg}")
        auth_failure("signup_error")

        # Обработка известных ошибок
        if "unique constraint" in error_msg.lower():
            if "users_email_key" in error_msg:
                raise HTTPException(status_code=400, detail="Email already registered")
            elif "users_username_key" in error_msg:
                raise HTTPException(status_code=400, detail="Username already taken")

        # Для отладки в разработке можно возвращать полное сообщение об ошибке
        if settings.environment.lower() == "development":
            raise HTTPException(status_code=500, detail=f"Internal server error: {error_msg}")
        else:
            # В продакшене скрываем детали ошибки
            raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/verify", summary="Verify email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """Confirm a user's email address using a verification token."""
    token_hash = hmac.new(
        settings.jwt.secret.encode(), token.encode(), hashlib.sha256
    ).hexdigest()
    result = await db.execute(
        select(UserToken).where(
            UserToken.token_hash == token_hash,
            UserToken.action == TokenAction.verify,
        )
    )
    user_token = result.scalars().first()
    if (
        not user_token
        or user_token.used_at
        or user_token.expires_at < datetime.utcnow()
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = await db.get(User, user_token.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    user.is_active = True
    user_token.used_at = datetime.utcnow()
    await db.commit()
    return {"message": "Email verified"}


async def _authenticate(db: AsyncSession, login: str, password: str) -> Token:
    if not login or not password:
        raise HTTPException(status_code=422, detail="username and password are required")

    # Логиним по username или email
    if "@" in login:
        query = select(User.id, User.password_hash, User.is_active).where(User.email == login)
    else:
        query = select(User.id, User.password_hash, User.is_active).where(User.username == login)

    result = await db.execute(query)
    row = result.first()
    if not row:
        auth_failure("user_not_found")
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    user_id, password_hash, is_active = row[0], row[1], row[2]
    if not is_active:
        auth_failure("inactive_user", user=str(user_id))
        raise HTTPException(status_code=400, detail="Email not verified")
    if not password_hash or not verify_password(password, password_hash):
        auth_failure("bad_password", user=str(user_id))
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    user_id_var.set(str(user_id))
    token = create_access_token(user_id)
    auth_success(str(user_id))
    return Token(access_token=token)


@router.post(
    "/login",
    response_model=Token,
    summary="User login",
    dependencies=[rate_limit_dep(settings.rate_limit.rules_login)],
)
async def login(request: Request, db: AsyncSession = Depends(get_db)):
    """Authenticate a user via form or JSON body and return a JWT token."""
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
    else:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
    return await _authenticate(db, username, password)


@router.post(
    "/login-json",
    response_model=Token,
    include_in_schema=True,
    summary="Login with JSON",
    dependencies=[rate_limit_dep(settings.rate_limit.rules_login_json)],
)
async def login_json(payload: LoginSchema, db: AsyncSession = Depends(get_db)):
    """Authenticate using a JSON payload instead of form data."""
    # Поддержка ручных JSON-вызовов
    return await _authenticate(db, payload.username, payload.password)


@router.post(
    "/change-password",
    summary="Change password",
    dependencies=[rate_limit_dep(settings.rate_limit.rules_change_password)],
)
async def change_password(
    payload: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the current user's password after verifying the old one."""
    if not current_user.password_hash or not verify_password(
        payload.old_password, current_user.password_hash
    ):
        raise HTTPException(status_code=400, detail="Incorrect password")
    current_user.password_hash = get_password_hash(payload.new_password)
    await db.commit()
    return {"message": "Password updated"}


@router.post(
    "/evm/nonce",
    summary="Request EVM nonce",
    dependencies=[rate_limit_dep(settings.rate_limit.rules_evm_nonce)],
)
async def evm_nonce(wallet_address: str):
    """Generate a nonce for the given wallet address to sign."""
    nonce = str(uuid.uuid4())
    nonce_store[wallet_address.lower()] = nonce
    return {"nonce": nonce}


@router.post(
    "/evm/verify",
    response_model=Token,
    summary="Verify EVM signature",
    dependencies=[rate_limit_dep(settings.rate_limit.rules_evm_verify)],
)
async def evm_verify(payload: EVMVerify, db: AsyncSession = Depends(get_db)):
    """Validate signed message from wallet and issue a JWT token."""
    stored_nonce = nonce_store.get(payload.wallet_address.lower())
    if not stored_nonce or stored_nonce not in payload.message:
        raise HTTPException(status_code=400, detail="Invalid nonce")
    message = encode_defunct(text=payload.message)
    try:
        recovered = w3.eth.account.recover_message(message, signature=payload.signature)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid signature")
    if recovered.lower() != payload.wallet_address.lower():
        raise HTTPException(status_code=400, detail="Signature mismatch")
    result = await db.execute(select(User).where(User.wallet_address == payload.wallet_address.lower()))
    user = result.scalars().first()
    if not user:
        user = User(wallet_address=payload.wallet_address.lower())
        db.add(user)
        await db.commit()
        await db.refresh(user)
    token = create_access_token(user.id)
    return Token(access_token=token)
