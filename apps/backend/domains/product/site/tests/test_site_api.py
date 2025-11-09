from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.iam import security as iam_security
from domains.platform.iam.application.facade import (
    csrf_protect,
    get_current_user,
    require_role_db,
)
from domains.product.site.api.admin_http import get_site_service, make_router
from domains.product.site.application import SiteService
from domains.product.site.domain import PageReviewStatus, PageType, SitePageNotFound


@pytest_asyncio.fixture()
async def api_client(service: SiteService):
    app = FastAPI()
    router = make_router()
    app.include_router(router)

    async def override_site_service() -> SiteService:
        return service

    async def allow_dependency(request=None) -> None:
        return None

    async def fake_user(request: Request) -> dict[str, str]:
        return {"role": "editor", "email": "tester@caves.dev", "sub": "tester"}

    original_security_get_user = iam_security.get_current_user
    iam_security.get_current_user = fake_user  # type: ignore[assignment]

    app.dependency_overrides[get_site_service] = override_site_service
    app.dependency_overrides[get_current_user] = fake_user
    app.dependency_overrides[csrf_protect] = allow_dependency
    for role in ("user", "editor"):
        app.dependency_overrides[require_role_db(role)] = allow_dependency
    skip_calls = {
        get_site_service,
        get_container,
        get_current_user,
        iam_security.get_current_user,
    }
    for route in router.routes:
        for dependency in route.dependant.dependencies:
            target = dependency.call
            if target in skip_calls:
                continue
            app.dependency_overrides[target] = allow_dependency

    dummy_container = SimpleNamespace(
        navigation_service=None,
        nodes_service=None,
        settings=SimpleNamespace(embedding_enabled=False),
    )
    app.dependency_overrides[get_container] = lambda: dummy_container

    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    client.headers["X-CSRF-Token"] = "test-token"
    client.headers["Authorization"] = "Bearer test-token"
    client.cookies.set("XSRF-TOKEN", "test-token")
    try:
        yield client
    finally:
        iam_security.get_current_user = original_security_get_user  # type: ignore[assignment]
        await client.aclose()


@pytest.mark.asyncio()
async def test_validate_page_draft_endpoint_success(
    service: SiteService,
    api_client: AsyncClient,
):
    page = await service.create_page(
        slug="/validate",
        page_type=PageType.LANDING,
        title="Validate",
        locale="ru",
        owner=None,
    )
    response = await api_client.post(
        f"/v1/site/pages/{page.id}/draft/validate",
        json={
            "data": {
                "blocks": [
                    {"id": "hero-1", "type": "hero", "enabled": True},
                    {"id": "list-1", "type": "nodes_carousel", "enabled": True},
                ]
            },
            "meta": {"title": "Preview"},
        },
    )
    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload["valid"] is True
    assert payload["data"]["blocks"][0]["id"] == "hero-1"
    assert payload["meta"]["title"] == "Preview"


@pytest.mark.asyncio()
async def test_validate_page_draft_endpoint_errors(
    service: SiteService,
    api_client: AsyncClient,
):
    page = await service.create_page(
        slug="/validate-errors",
        page_type=PageType.LANDING,
        title="Validate errors",
        locale="ru",
        owner=None,
    )
    response = await api_client.post(
        f"/v1/site/pages/{page.id}/draft/validate",
        json={
            "data": {
                "blocks": [
                    {"id": "hero-1", "type": "hero", "enabled": True},
                    {"id": "hero-1", "type": "hero", "enabled": True},
                ]
            }
        },
    )
    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload["valid"] is False
    assert payload["code"] == "site_page_validation_failed"
    assert "hero-1" in payload["errors"]["blocks"]


@pytest.mark.asyncio()
async def test_diff_page_draft_endpoint(
    service: SiteService,
    api_client: AsyncClient,
):
    page = await service.create_page(
        slug="/diff-api",
        page_type=PageType.LANDING,
        title="Diff API",
        locale="ru",
        owner=None,
    )
    initial = await service.get_page_draft(page.id)
    await service.save_page_draft(
        page_id=page.id,
        payload={
            "blocks": [
                {"id": "hero-1", "type": "hero", "enabled": True},
            ]
        },
        meta={"title": "First"},
        comment=None,
        review_status=PageReviewStatus.NONE,
        expected_version=initial.version,
        actor=None,
    )
    await service.publish_page(page_id=page.id, actor=None, comment=None, diff=None)
    draft_after_publish = await service.get_page_draft(page.id)
    await service.save_page_draft(
        page_id=page.id,
        payload={
            "blocks": [
                {"id": "hero-1", "type": "hero", "enabled": True, "title": "Updated"},
                {"id": "promo-1", "type": "recommendations", "enabled": True},
            ]
        },
        meta={"title": "Second"},
        comment=None,
        review_status=PageReviewStatus.PENDING,
        expected_version=draft_after_publish.version,
        actor=None,
    )
    response = await api_client.get(f"/v1/site/pages/{page.id}/draft/diff")
    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload["draft_version"] >= draft_after_publish.version + 1
    assert payload["published_version"] == 1
    diff_signatures = {
        (
            entry.get("type"),
            entry.get("blockId") or entry.get("field"),
            entry.get("change"),
        )
        for entry in payload["diff"]
    }
    assert ("block", "hero-1", "updated") in diff_signatures or (
        "data",
        "locales",
        "updated",
    ) in diff_signatures
    assert ("block", "promo-1", "added") in diff_signatures or (
        "data",
        "locales",
        "updated",
    ) in diff_signatures


@pytest.mark.asyncio()
async def test_preview_page_endpoint(
    service: SiteService,
    api_client: AsyncClient,
):
    page = await service.create_page(
        slug="/preview-api",
        page_type=PageType.LANDING,
        title="Preview API",
        locale="ru",
        owner=None,
    )
    draft = await service.get_page_draft(page.id)
    await service.save_page_draft(
        page_id=page.id,
        payload={
            "blocks": [
                {"id": "hero-1", "type": "hero", "enabled": True, "title": "Hero"},
            ]
        },
        meta={"title": "Preview API"},
        comment=None,
        review_status=PageReviewStatus.NONE,
        expected_version=draft.version,
        actor=None,
    )
    response = await api_client.post(
        f"/v1/site/pages/{page.id}/preview",
        json={
            "layouts": ["mobile"],
        },
    )
    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload["page"]["slug"] == "/preview-api"
    assert payload["page"]["pinned"] is False
    assert payload["version_mismatch"] is False
    assert "mobile" in payload["layouts"]
    mobile_layout = payload["layouts"]["mobile"]
    assert mobile_layout["data"]["blocks"][0]["id"] == "hero-1"
    assert mobile_layout["payload"]["blocks"][0]["title"] == "Hero"
    assert mobile_layout["payload"]["meta"]["preview"]["mode"] == "site_preview"


@pytest.mark.asyncio()
async def test_block_preview_endpoint(
    api_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    sample = {
        "block": "recommendations",
        "locale": "ru",
        "source": "live",
        "fetched_at": "2025-10-26T11:00:00Z",
        "items": [{"title": "Sample", "href": "/n/sample"}],
        "meta": {"mode": "site_preview"},
    }

    async def fake_preview(container, block_id, *, locale, limit):
        assert block_id == "recommendations"
        assert locale == "ru"
        assert limit == 5
        return sample

    monkeypatch.setattr(
        "domains.product.site.api.admin_http.build_block_preview",
        fake_preview,
    )

    response = await api_client.get(
        "/v1/site/blocks/recommendations/preview?locale=ru&limit=5",
    )
    assert response.status_code == 200
    assert response.json() == sample


@pytest.mark.asyncio()
async def test_page_detail_includes_block_refs(
    service: SiteService,
    api_client: AsyncClient,
) -> None:
    block = await service.create_global_block(
        key="header-nav",
        title="Header Nav",
        section="header",
        locale="ru",
        requires_publisher=True,
        data={},
        meta={},
    )
    page = await service.create_page(
        slug="/page-with-header",
        page_type=PageType.LANDING,
        title="Page With Header",
        locale="ru",
        owner=None,
    )
    draft = await service.get_page_draft(page.id)
    await service.save_page_draft(
        page_id=page.id,
        payload={"blocks": []},
        meta={},
        comment=None,
        review_status=PageReviewStatus.NONE,
        expected_version=draft.version,
        actor="editor@example.com",
    )
    await service.assign_shared_block(
        page_id=page.id,
        section="header",
        block_id=block.id,
    )

    detail_response = await api_client.get(f"/v1/site/pages/{page.id}")
    assert detail_response.status_code == 200, detail_response.json()
    detail_payload = detail_response.json()
    assert "shared_bindings" in detail_payload
    assert any(item["key"] == block.key for item in detail_payload["shared_bindings"] or [])
    assert any(item["key"] == block.key for item in detail_payload.get("block_refs") or [])

    draft_response = await api_client.get(f"/v1/site/pages/{page.id}/draft")
    assert draft_response.status_code == 200
    draft_payload = draft_response.json()
    assert any(item["key"] == block.key for item in draft_payload.get("shared_bindings") or [])
    assert any(item["key"] == block.key for item in draft_payload.get("block_refs") or [])


@pytest.mark.asyncio()
async def test_update_page_endpoint_success(
    service: SiteService,
    api_client: AsyncClient,
):
    slug_base = uuid4().hex
    new_slug = f"/update-target-new-{slug_base}"
    page = await service.create_page(
        slug=f"/update-target-{slug_base}",
        page_type=PageType.LANDING,
        title="Update Target",
        locale="ru",
        owner="content",
    )
    response = await api_client.patch(
        f"/v1/site/pages/{page.id}",
        json={
            "slug": new_slug,
            "title": "Update Target New",
            "pinned": True,
        },
    )
    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload["slug"] == new_slug
    assert payload["title"] == "Update Target New"
    assert payload["pinned"] is True

    refreshed = await service.get_page(page.id)
    assert refreshed.slug == new_slug
    assert refreshed.title == "Update Target New"
    assert refreshed.pinned is True


@pytest.mark.asyncio()
async def test_update_page_endpoint_conflict(
    service: SiteService,
    api_client: AsyncClient,
):
    first_slug = f"/update-conflict-first-{uuid4().hex}"
    second_slug = f"/update-conflict-second-{uuid4().hex}"
    await service.create_page(
        slug=first_slug,
        page_type=PageType.LANDING,
        title="Update Conflict First",
        locale="ru",
        owner=None,
    )
    second = await service.create_page(
        slug=second_slug,
        page_type=PageType.LANDING,
        title="Update Conflict Second",
        locale="ru",
        owner=None,
    )
    response = await api_client.patch(
        f"/v1/site/pages/{second.id}",
        json={"slug": first_slug},
    )
    assert response.status_code == 409
    payload = response.json()
    assert payload.get("detail") == "site_page_update_conflict"


@pytest.mark.asyncio()
async def test_delete_page_endpoint_success(
    service: SiteService,
    api_client: AsyncClient,
):
    slug = f"/delete-via-api-{uuid4().hex}"
    page = await service.create_page(
        slug=slug,
        page_type=PageType.LANDING,
        title="Delete via API",
        locale="ru",
        owner=None,
    )
    response = await api_client.delete(f"/v1/site/pages/{page.id}")
    assert response.status_code == 204
    with pytest.raises(SitePageNotFound):
        await service.get_page(page.id)


@pytest.mark.asyncio()
async def test_delete_page_endpoint_forbidden_for_pinned(
    service: SiteService,
    api_client: AsyncClient,
):
    slug = f"/delete-blocked-{uuid4().hex}"
    page = await service.create_page(
        slug=slug,
        page_type=PageType.LANDING,
        title="Cannot delete",
        locale="ru",
        owner=None,
        pinned=True,
    )
    response = await api_client.delete(f"/v1/site/pages/{page.id}")
    assert response.status_code == 409


@pytest.mark.asyncio()
async def test_blocks_archive_endpoint(
    service: SiteService,
    api_client: AsyncClient,
):
    block = await service.create_global_block(
        key=f"archive-api-{uuid4().hex[:6]}",
        title="Archive via API",
        section="promo",
        locale="ru",
        requires_publisher=False,
        data={},
        meta={},
    )
    response = await api_client.post(
        f"/v1/site/blocks/{block.id}/archive",
        json={},
    )
    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload["block"]["status"] == "archived"


@pytest.mark.asyncio()
async def test_components_list_endpoint(api_client: AsyncClient) -> None:
    response = await api_client.get("/v1/site/components")
    assert response.status_code == 200, response.json()
    payload = response.json()
    assert isinstance(payload.get("items"), list)
    header_entry = next(
        (item for item in payload["items"] if item["key"] == "header"),
        None,
    )
    assert header_entry is not None
    assert header_entry["schema_url"].endswith("/components/header/schema")


@pytest.mark.asyncio()
async def test_component_schema_endpoint(api_client: AsyncClient) -> None:
    response = await api_client.get("/v1/site/components/header/schema")
    assert response.status_code == 200, response.text
    assert "etag" in response.headers
    schema = response.json()
    assert schema["title"]
    assert schema["type"] == "object"


@pytest.mark.asyncio()
async def test_block_detail_includes_component_schema(
    service: SiteService,
    api_client: AsyncClient,
) -> None:
    block = await service.create_global_block(
        key=f"header-detail-{uuid4().hex[:6]}",
        title="Header Detail",
        section="header",
        locale="ru",
        requires_publisher=False,
        data={},
        meta={},
    )
    await service.save_global_block(
        block_id=block.id,
        payload={
            "locales": {
                "ru": {"title": "Главная"},
            }
        },
        meta={},
        version=block.draft_version,
        comment=None,
        review_status=PageReviewStatus.NONE,
        actor=None,
        available_locales=["ru", "en"],
    )
    response = await api_client.get(f"/v1/site/blocks/{block.id}")
    assert response.status_code == 200, response.json()
    payload = response.json()
    block_payload = payload["block"]
    assert block_payload["component_schema"]["key"] == "header"
    assert block_payload["component_schema"]["schema_url"].endswith("/components/header/schema")
    locales = block_payload["locale_statuses"]
    assert any(entry["locale"] == "ru" and entry["status"] == "ready" for entry in locales)
    assert any(entry["locale"] == "en" and entry["status"] == "missing" for entry in locales)
