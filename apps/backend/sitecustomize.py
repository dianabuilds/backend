from __future__ import annotations

"""Process-wide tweaks applied as soon as Python starts.

The file is imported automatically by the stdlib `site` module. We use it to
force the selector event loop policy on Windows so asyncio TLS (asyncpg) is
stable. Uvicorn configures the event loop before importing our FastAPI app,
so doing this in app code is too late -- it must happen at interpreter boot.
"""

import asyncio
import logging
import sys

logger = logging.getLogger("sitecustomize")


def _apply_windows_selector_policy() -> None:
    if not sys.platform.lower().startswith("win"):
        return

    selector_factory = getattr(asyncio, "WindowsSelectorEventLoopPolicy", None)
    proactor_cls = getattr(asyncio, "WindowsProactorEventLoopPolicy", None)
    if selector_factory is None:
        logger.warning(
            "Windows selector event loop policy is unavailable; async TLS may fail"
        )
        return

    current = asyncio.get_event_loop_policy()
    if proactor_cls is not None and not isinstance(current, proactor_cls):
        return

    try:
        asyncio.set_event_loop_policy(selector_factory())
    except Exception:  # pragma: no cover - defensive logging only
        logger.exception("Failed to enforce Windows selector event loop policy")
    else:
        logger.info("Windows selector event loop policy applied via sitecustomize")


_apply_windows_selector_policy()


__all__ = ["_apply_windows_selector_policy"]
