from __future__ import annotations

import argparse
import asyncio
import inspect
import logging
import os
import signal
import sys
from collections.abc import Sequence

from packages.core.config import load_settings

from .registry import (
    WorkerRuntimeContext,
    get_worker_builder,
    list_registered_workers,
)


async def run_worker(name: str, *, log_level: str | None = None) -> None:
    env = dict(os.environ)
    level_name = (log_level or env.get("WORKER_LOG_LEVEL") or "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level_name, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logger = logging.getLogger(f"worker.{name}")
    settings = load_settings()

    builder = get_worker_builder(name)
    context = WorkerRuntimeContext(settings=settings, env=env, logger=logger)
    worker_or_awaitable = builder(context)
    worker = (
        await worker_or_awaitable
        if inspect.isawaitable(worker_or_awaitable)
        else worker_or_awaitable
    )

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _request_stop(sig: signal.Signals) -> None:
        logger.info("received signal %s, shutting down", sig.name)
        stop_event.set()

    for sig in _iter_signals():
        try:
            loop.add_signal_handler(sig, _request_stop, sig)
        except (NotImplementedError, RuntimeError):  # pragma: no cover - Windows fallback
            signal.signal(sig, lambda *_args, _sig=sig: _request_stop(_sig))

    logger.info("starting worker '%s'", name)
    try:
        await worker.run(stop_event)
    except asyncio.CancelledError:  # pragma: no cover - forwarded cancellation
        raise
    finally:
        logger.info("stopping worker '%s'", name)
        try:
            await worker.shutdown()
        finally:
            stop_event.set()


def _iter_signals() -> list[signal.Signals]:  # pragma: no cover - helper
    signals: list[signal.Signals] = [signal.SIGINT]
    if hasattr(signal, "SIGTERM"):
        signals.append(signal.SIGTERM)
    if hasattr(signal, "SIGBREAK"):
        signals.append(signal.SIGBREAK)
    return signals


def _ensure_event_loop_policy() -> None:
    if sys.platform.startswith("win") and hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        policy = asyncio.get_event_loop_policy()
        if not isinstance(policy, asyncio.WindowsSelectorEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run a registered worker")
    parser.add_argument("--name", help="worker name", default=os.getenv("WORKER_NAME"))
    parser.add_argument(
        "--log-level", help="override log level", default=os.getenv("WORKER_LOG_LEVEL")
    )
    args = parser.parse_args(argv)

    if not args.name:
        available = ", ".join(list_registered_workers()) or "<none>"
        parser.error(f"--name is required. available workers: {available}")

    try:
        _ensure_event_loop_policy()
        asyncio.run(run_worker(args.name, log_level=args.log_level))
    except KeyboardInterrupt:  # pragma: no cover
        pass


__all__ = ["main", "run_worker"]
