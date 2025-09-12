from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class MenuItem(BaseModel):
    id: str
    label: str
    path: str | None = None
    icon: str | None = None
    order: int = 100
    children: list["MenuItem"] = Field(default_factory=list)
    roles: list[str] | None = None
    feature_flag: str | None = Field(default=None, alias="featureFlag")
    external: bool = False
    divider: bool = False
    hidden: bool = False

    model_config = {"populate_by_name": True}


class MenuResponse(BaseModel):
    items: list[MenuItem]
    version: str
    generated_at: datetime = Field(alias="generatedAt")

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def _validate(self):
        ids: set[str] = set()

        def walk(items: list[MenuItem], depth: int) -> None:
            if not items:
                return
            if depth > 3:
                raise ValueError("menu depth exceeds 3")
            for item in items:
                if item.id in ids:
                    raise ValueError(f"duplicate id: {item.id}")
                ids.add(item.id)
                walk(item.children, depth + 1)

        walk(self.items, 1)
        return self

__all__ = ["MenuItem", "MenuResponse"]

