from pydantic import BaseModel, EmailStr


class SignupSchema(BaseModel):
    email: EmailStr
    password: str
    username: str | None = None


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePassword(BaseModel):
    old_password: str
    new_password: str


class EVMVerify(BaseModel):
    message: str
    signature: str
    wallet_address: str
