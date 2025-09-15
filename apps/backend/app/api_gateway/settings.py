from __future__ import annotations

from pydantic import BaseModel


class Settings(BaseModel):
    env: str = "dev"
    database_url: str = "postgresql://app:app@localhost:5432/app"
