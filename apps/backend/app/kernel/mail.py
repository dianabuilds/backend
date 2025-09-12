from __future__ import annotations

import abc
from typing import Iterable, Mapping, Optional


class AbstractMailService(abc.ABC):
    @abc.abstractmethod
    async def send(
        self,
        to: Iterable[str],
        subject: str,
        text_body: Optional[str] = None,
        html_body: Optional[str] = None,
        *,
        sender: Optional[str] = None,
        cc: Optional[Iterable[str]] = None,
        bcc: Optional[Iterable[str]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        pass

    @abc.abstractmethod
    async def close(self) -> None:
        pass


__all__ = ["AbstractMailService"]

