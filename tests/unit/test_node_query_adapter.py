from __future__ import annotations

import importlib
import sys
from unittest.mock import AsyncMock, patch

import pytest

# Ensure app package resolves
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)


@patch("app.domains.nodes.infrastructure.queries.node_query_adapter.NodeQueryService")
@pytest.mark.asyncio
async def test_node_query_adapter_delegates(NodeQueryServiceMock):
    from app.domains.nodes.application.query_models import (
        NodeFilterSpec,
        PageRequest,
        QueryContext,
    )
    from app.domains.nodes.infrastructure.queries.node_query_adapter import (
        NodeQueryAdapter,
    )

    svc_instance = NodeQueryServiceMock.return_value
    svc_instance.list_nodes = AsyncMock()
    svc_instance.compute_nodes_etag = AsyncMock(return_value="etag")

    adapter = NodeQueryAdapter(db=object())
    spec = NodeFilterSpec()
    page = PageRequest()
    ctx = QueryContext(user=None, is_admin=True)

    await adapter.list_nodes(spec, page, ctx)
    svc_instance.list_nodes.assert_awaited_once_with(spec, page, ctx)

    await adapter.compute_nodes_etag(spec, ctx, page)
    svc_instance.compute_nodes_etag.assert_awaited_once_with(spec, ctx, page)
