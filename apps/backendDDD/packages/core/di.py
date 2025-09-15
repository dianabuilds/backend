from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass
class Provider:
    factory: Callable[[], object]


class ContainerLite:
    def __init__(self) -> None:
        self._registry: dict[str, Provider] = {}

    def register(self, key: str, factory: Callable[[], object]) -> None:
        self._registry[key] = Provider(factory=factory)

    def resolve(self, key: str) -> object:
        return self._registry[key].factory()
