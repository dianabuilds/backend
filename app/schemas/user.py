from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    id: UUID
    created_at: datetime
    email: EmailStr | None = None
    wallet_address: str | None = None
    is_active: bool
    username: str | None = None
    bio: str | None = None
    avatar_url: str | None = None

    model_config = {
        "from_attributes": True
    }


class UserOut(UserBase):
    pass


class UserUpdate(BaseModel):
    username: str | None = None
    bio: str | None = None
    avatar_url: str | None = None


class UserPremiumUpdate(BaseModel):
    is_premium: bool
    premium_until: datetime | None = None
