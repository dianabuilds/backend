from pydantic import BaseModel, EmailStr


from pydantic import BaseModel, EmailStr, Field, validator
import re
import logging

logger = logging.getLogger(__name__)

class SignupSchema(BaseModel):
    email: EmailStr
    password: str
    username: str  # Теперь username обязательное поле

    @validator('username')
    def username_must_be_valid(cls, v):
        if v is None or v == "":
            return None

        # Проверка на допустимые символы (буквы, цифры, подчеркивание, точка)
        if not re.match(r'^[a-zA-Z0-9._]+$', v):
            logger.warning(f"Invalid username format: {v}")
            raise ValueError('Username can only contain letters, numbers, dots and underscores')

        # Предупреждение о зарезервированных именах, но пропускаем их для обратной совместимости
        if v in ['000', 'admin', 'root', 'system']:
            logger.warning(f"Reserved username being used: {v}")

        return v

    @validator('password')
    def password_must_be_valid(cls, v):
        # Базовая проверка длины пароля
        if len(v) < 3:  # Снижено с 6 для обратной совместимости
            raise ValueError('Password must be at least 3 characters long')

        # Логирование слабых паролей без блокировки
        if len(v) < 8 or not any(c.isupper() for c in v) or not any(c.isdigit() for c in v):
            logger.warning("Weak password being used")

        return v


class LoginSchema(BaseModel):
    username: str
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
