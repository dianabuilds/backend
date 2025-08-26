from __future__ import annotations

from pydantic import BaseModel


class UserAIPrefOut(BaseModel):
    model: str | None = None


class UserAIPrefIn(BaseModel):
    model: str


__all__ = ["UserAIPrefOut", "UserAIPrefIn"]
