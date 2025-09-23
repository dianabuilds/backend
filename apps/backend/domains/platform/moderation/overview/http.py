from __future__ import annotations

from urllib.parse import parse_qsl, urlsplit, urlunsplit

from apps.backend import get_container
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from packages.core.config import to_async_dsn

from ..dtos import OverviewDTO
from ..rbac import require_scopes

router = APIRouter(prefix="/overview", tags=["moderation-overview"])


@router.get(
    "",
    response_model=OverviewDTO,
    dependencies=[Depends(require_scopes("moderation:overview:read"))],
)
async def get_overview(limit: int = 10, container=Depends(get_container)) -> OverviewDTO:
    complaints_new: dict[str, object] = {}
    tickets: dict[str, object] = {}
    content_queues: dict[str, int] = {}
    try:
        dsn = to_async_dsn(container.settings.database_url)
        if not dsn:
            return OverviewDTO(
                complaints_new=complaints_new,
                tickets=tickets,
                content_queues=content_queues,
                last_sanctions=[],
                charts={},
                cards=[],
            )
        u = urlsplit(dsn)
        qdict = {k.lower(): v for k, v in parse_qsl(u.query, keep_blank_values=True)}
        ssl_flag = None
        if "ssl" in qdict:
            ssl_flag = str(qdict["ssl"]).strip().lower() in {"1", "true", "yes"}
        dsn_no_query = urlunsplit((u.scheme, u.netloc, u.path, "", u.fragment))
        connect_args = {"connect_args": {}}  # type: ignore[var-annotated]
        if ssl_flag is not None:
            connect_args = {"connect_args": {"ssl": ssl_flag}}
        eng = create_async_engine(dsn_no_query, future=True, **connect_args)
        async with eng.begin() as conn:
            try:
                rows = (
                    (
                        await conn.execute(
                            text("SELECT status, count(*) as c FROM nodes GROUP BY status")
                        )
                    )
                    .mappings()
                    .all()
                )
                for r in rows:
                    st = str(r.get("status") or "")
                    if st:
                        content_queues[st] = int(r.get("c") or 0)
            except Exception:
                pass
    except Exception:
        pass
    return OverviewDTO(
        complaints_new=complaints_new,
        tickets=tickets,
        content_queues=content_queues,
        last_sanctions=[],
        charts={},
        cards=[],
    )


__all__ = ["router"]
