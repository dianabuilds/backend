import pytest
from httpx import AsyncClient

from app.domains.accounts.api import router as accounts_router
from app.domains.nodes.content_admin_router import router as nodes_router
from app.main import app

app.include_router(accounts_router)
app.include_router(nodes_router)

pytestmark = pytest.mark.skip("requires full database schema")


@pytest.mark.asyncio
async def test_account_node_simulation_trace(client: AsyncClient, auth_headers: dict[str, str]):
    # Create account
    resp = await client.post(
        "/admin/accounts",
        json={"name": "Test WS", "slug": "test-ws"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    acc = resp.json()
    account_id = acc["id"]

    # Create node
    resp = await client.post(
        f"/admin/accounts/{account_id}/nodes/types/quest",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    node = resp.json()
    node_id = node["id"]

    # Simulate node
    resp = await client.post(
        f"/admin/accounts/{account_id}/nodes/types/quest/{node_id}/simulate",
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
