from __future__ import annotations

from fastapi import Request


def get_container(req: Request):
    return req.app.state.container  # type: ignore[attr-defined]
