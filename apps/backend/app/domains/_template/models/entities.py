from __future__ import annotations

"""Доменные сущности/VO, если нужны поверх ORM.

В большинстве случаев ORM-модели лежат в `infrastructure/models`,
а здесь можно держать чистые объекты/инварианты.
"""

from dataclasses import dataclass


@dataclass(slots=True)
class ExampleEntity:
    id: int
    name: str

