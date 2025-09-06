import pytest
from httpx import AsyncClient

from app.domains.nodes.content_admin_router import router as nodes_router
from app.domains.workspaces.api import router as workspaces_router
from app.main import app

app.include_router(workspaces_router)
app.include_router(nodes_router)

pytestmark = pytest.mark.skip("requires full database schema")


@pytest.mark.asyncio
async def test_workspace_node_simulation_trace(client: AsyncClient, auth_headers: dict[str, str]):
    # Create workspace
    resp = await client.post(
        "/admin/workspaces",
        json={"name": "Test WS", "slug": "test-ws"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    ws = resp.json()
    ws_id = ws["id"]

    # Create node
    resp = await client.post(
        f"/admin/accounts/{ws_id}/nodes/types/quest",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    node = resp.json()
    node_id = node["id"]

    # Simulate node
    resp = await client.post(
        f"/admin/accounts/{ws_id}/nodes/types/quest/{node_id}/simulate",
        json={"inputs": {}},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    sim = resp.json()
    assert "result" in sim

    # Create trace
    resp = await client.post(
        "/traces",
        json={"node_id": node_id, "kind": "manual", "comment": "ok"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    trace = resp.json()

    # List traces for node
    resp = await client.get(f"/traces?node_id={node_id}", headers=auth_headers)
    assert resp.status_code == 200
    traces = resp.json()
    assert any(t["id"] == trace["id"] for t in traces)
