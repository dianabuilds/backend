from __future__ import annotations

from pydantic import BaseModel


class SearchTopQuery(BaseModel):
    query: str
    count: int
    results: int
