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


@router.post("/signup", response_model=Token)
async def signup(payload: SignupSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email,
        username=payload.username,
        password_hash=get_password_hash(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(user.id)
    return Token(access_token=token)


@router.post("/login", response_model=Token)
async def login(payload: LoginSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalars().first()
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
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
