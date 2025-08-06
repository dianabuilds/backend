import uuid

from eth_account.messages import encode_defunct
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from web3.auto import w3

from app.api.deps import get_current_user
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePassword,
    EVMVerify,
    LoginSchema,
    SignupSchema,
    Token,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# simple in-memory nonce store
nonce_store: dict[str, str] = {}


import logging

logger = logging.getLogger(__name__)

@router.post("/signup", response_model=Token)
async def signup(payload: SignupSchema, db: AsyncSession = Depends(get_db)):
    logger.info(f"Signup attempt for email: {payload.email} with username: {payload.username}")

    # Проверка на пустые значения
    if not payload.email or not payload.password or not payload.username:
        logger.warning("Signup attempt with empty email, username or password")
        raise HTTPException(status_code=400, detail="Email, username and password are required")

    # Проверка на существующий email
    email_result = await db.execute(select(User).where(User.email == payload.email))
    if email_result.scalars().first():
        logger.warning(f"Signup attempt with existing email: {payload.email}")
        raise HTTPException(status_code=400, detail="Email already registered")

    # Проверка на существующий username
    username_result = await db.execute(select(User).where(User.username == payload.username))
    if username_result.scalars().first():
        logger.warning(f"Signup attempt with existing username: {payload.username}")
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

        # Создаем токен
        token = create_access_token(user.id)
        logger.info(f"User created successfully: {user.id}")

        return Token(access_token=token)
    except Exception as e:
        await db.rollback()
        error_msg = str(e)
        logger.error(f"Error during user creation: {error_msg}")

        # Обработка известных ошибок
        if "unique constraint" in error_msg.lower():
            if "users_email_key" in error_msg:
                raise HTTPException(status_code=400, detail="Email already registered")
            elif "users_username_key" in error_msg:
                raise HTTPException(status_code=400, detail="Username already taken")

        # Для отладки в разработке можно возвращать полное сообщение об ошибке
        if settings.ENVIRONMENT.lower() == "development":
            raise HTTPException(status_code=500, detail=f"Internal server error: {error_msg}")
        else:
            # В продакшене скрываем детали ошибки
            raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login", response_model=Token)
async def login(payload: LoginSchema, db: AsyncSession = Depends(get_db)):
    # Поиск пользователя по имени пользователя
    result = await db.execute(select(User).where(User.username == payload.username))
    user = result.scalars().first()

    # Проверка пользователя и пароля
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # Создание токена
    token = create_access_token(user.id)
    return Token(access_token=token)


@router.post("/change-password")
async def change_password(
    payload: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.password_hash or not verify_password(
        payload.old_password, current_user.password_hash
    ):
        raise HTTPException(status_code=400, detail="Incorrect password")
    current_user.password_hash = get_password_hash(payload.new_password)
    await db.commit()
    return {"message": "Password updated"}


@router.post("/evm/nonce")
async def evm_nonce(wallet_address: str):
    nonce = str(uuid.uuid4())
    nonce_store[wallet_address.lower()] = nonce
    return {"nonce": nonce}


@router.post("/evm/verify", response_model=Token)
async def evm_verify(payload: EVMVerify, db: AsyncSession = Depends(get_db)):
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
