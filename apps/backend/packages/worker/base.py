from __future__ import annotations

import asyncio
import logging
import secrets
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

_secure_random = secrets.SystemRandom()


class Worker(ABC):
    """Abstract worker contract.

    Concrete workers implement :meth:`run`, honouring the provided stop event.
    """

    def __init__(self, name: str, *, logger: logging.Logger | None = None) -> None:
        self.name = name
        self._logger = logger or logging.getLogger(name)

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @abstractmethod
    async def run(self, stop_event: asyncio.Event) -> None:
        """Run until the ``stop_event`` is set."""

    async def shutdown(self) -> None:  # pragma: no cover - default no-op
        """Hook for graceful shutdown logic."""
        return None


@dataclass(slots=True)
class PeriodicWorkerConfig:
    interval: float
    jitter: float = 0.0
    immediate: bool = False


class PeriodicWorker(Worker):
    """Generic periodic worker calling ``callback`` every ``interval`` seconds."""

    def __init__(
        self,
        name: str,
        callback: Callable[[], Awaitable[None]],
        *,
        config: PeriodicWorkerConfig,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(name, logger=logger)
        self._callback = callback
        self._config = config

    async def run(self, stop_event: asyncio.Event) -> None:
        interval = max(0.1, float(self._config.interval))
        jitter = max(0.0, float(self._config.jitter))
        if self._config.immediate:
            await self._invoke()
        while not stop_event.is_set():
            await self._sleep(interval, jitter, stop_event)
            if stop_event.is_set():
                break
            await self._invoke()

    async def _invoke(self) -> None:
        try:
            await self._callback()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.exception("worker iteration failed: %s", exc)

    async def _sleep(
        self, interval: float, jitter: float, stop_event: asyncio.Event
    ) -> None:
        delay = interval
        if jitter > 0:
            delay += _secure_random.uniform(-jitter, jitter)
        delay = max(0.1, delay)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=delay)
        except TimeoutError:
            return


__all__ = ["Worker", "PeriodicWorker", "PeriodicWorkerConfig"]
