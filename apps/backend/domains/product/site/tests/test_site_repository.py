import json
from collections.abc import Mapping
from typing import Any

import pytest

from domains.product.site.application import SiteService
from domains.product.site.domain import (
    GlobalBlockStatus,
    PageReviewStatus,
    PageStatus,
    PageType,
    SitePageNotFound,
    SiteRepositoryError,
    SiteValidationError,
)


def _snapshot_to_dict(snapshot: Any) -> dict[str, Any]:
    if isinstance(snapshot, str):
        try:
            decoded = json.loads(snapshot)
        except json.JSONDecodeError:
            return {}
        if isinstance(decoded, Mapping):
            return dict(decoded)
        return {}
    if isinstance(snapshot, Mapping):
        return dict(snapshot)
    return {}


@pytest.mark.asyncio()
async def test_create_and_list_page(service: SiteService):
    created = await service.create_page(
        slug="/",
        page_type=PageType.LANDING,
        title="Главная",
        locale="ru",
        owner="team",
    )
    assert created.slug == "/"
    assert created.status == PageStatus.DRAFT
    assert created.pinned is False

    pages, total = await service.list_pages()
    assert total == 1
    assert pages[0].slug == "/"
    assert pages[0].pinned is False


@pytest.mark.asyncio()
async def test_update_page_allows_editing_metadata(service: SiteService):
    page = await service.create_page(
        slug="/editable",
        page_type=PageType.LANDING,
        title="Editable",
        locale="ru",
        owner="content",
    )
    updated = await service.update_page(
        page_id=page.id,
        slug="/editable-updated",
        title="Editable Updated",
        owner="marketing",
        pinned=True,
        actor="editor@example.com",
    )
    assert updated.slug == "/editable-updated"
    assert updated.title == "Editable Updated"
    assert updated.owner == "marketing"
    assert updated.pinned is True

    audit_rows, _ = await service.list_audit(
        entity_type="page", entity_id=page.id, limit=5
    )
    actions = {row["action"] for row in audit_rows}
    assert "update" in actions


@pytest.mark.asyncio()
async def test_update_page_conflict_on_duplicate_slug(service: SiteService):
    first = await service.create_page(
        slug="/conflict-source",
        page_type=PageType.LANDING,
        title="Conflict Source",
        locale="ru",
        owner=None,
    )
    second = await service.create_page(
        slug="/conflict-target",
        page_type=PageType.LANDING,
        title="Conflict Target",
        locale="ru",
        owner=None,
    )
    with pytest.raises(SiteRepositoryError) as excinfo:
        await service.update_page(
            page_id=second.id,
            slug=first.slug,
            actor="editor@example.com",
        )
    assert str(excinfo.value) == "site_page_update_conflict"


@pytest.mark.asyncio()
async def test_list_pages_supports_pinned_filters(service: SiteService):
    pinned_page = await service.create_page(
        slug="/pinned",
        page_type=PageType.LANDING,
        title="Pinned Page",
        locale="ru",
        owner=None,
        pinned=True,
    )
    await service.create_page(
        slug="/regular",
        page_type=PageType.LANDING,
        title="Regular Page",
        locale="ru",
        owner=None,
    )
    pinned_items, total_pinned = await service.list_pages(pinned=True)
    assert total_pinned == 1
    assert pinned_items[0].id == pinned_page.id
    assert pinned_items[0].pinned is True

    unpinned_items, total_unpinned = await service.list_pages(pinned=False)
    assert total_unpinned >= 1
    assert all(not item.pinned for item in unpinned_items)


@pytest.mark.asyncio()
async def test_delete_page_removes_usage(service: SiteService):
    page = await service.create_page(
        slug="/deletable",
        page_type=PageType.LANDING,
        title="Deletable",
        locale="ru",
        owner="marketing",
    )
    block = await service.create_global_block(
        key="header-delete",
        title="Header Delete",
        section="header",
        locale="ru",
        requires_publisher=False,
        actor="tester",
    )
    await service.save_page_draft(
        page_id=page.id,
        payload={"blocks": []},
        meta={"globalBlocks": {"header": block.key}},
        comment=None,
        review_status=PageReviewStatus.NONE,
        expected_version=1,
        actor="tester",
    )

    usage_before = await service.list_block_usage(block.id)
    assert any(item.page_id == page.id for item in usage_before)

    await service.delete_page(page.id, actor="tester")

    with pytest.raises(SitePageNotFound):
        await service.get_page(page.id)

    usage_after = await service.list_block_usage(block.id)
    assert all(item.page_id != page.id for item in usage_after)
    refreshed_block = await service.get_global_block(block.id)
    assert refreshed_block.usage_count in (0, None)


@pytest.mark.asyncio()
async def test_delete_page_forbidden_for_pinned(service: SiteService):
    page = await service.create_page(
        slug="/pinned-delete",
        page_type=PageType.LANDING,
        title="Pinned Delete",
        locale="ru",
        owner=None,
        pinned=True,
    )
    with pytest.raises(SiteRepositoryError):
        await service.delete_page(page.id, actor="tester")

    ordered_items, _ = await service.list_pages(sort="pinned_desc")
    assert ordered_items[0].pinned is True
    assert page.id in {item.id for item in ordered_items}


@pytest.mark.asyncio()
async def test_page_global_block_usage_updates_with_draft(service: SiteService):
    header_block = await service.create_global_block(
        key="header-nav",
        title="Header Nav",
        section="header",
        locale="ru",
        requires_publisher=True,
        data={},
        meta={},
    )
    page = await service.create_page(
        slug="/with-header",
        page_type=PageType.LANDING,
        title="With Header",
        locale="ru",
        owner=None,
    )
    draft = await service.get_page_draft(page.id)
    await service.save_page_draft(
        page_id=page.id,
        payload={"blocks": []},
        meta={"globalBlocks": {"header": header_block.key}},
        comment=None,
        review_status=PageReviewStatus.NONE,
        expected_version=draft.version,
        actor="editor@example.com",
    )
    links = await service.list_page_global_blocks(page.id)
    assert links
    assert any(link["key"] == header_block.key for link in links)
    assert any(link["section"] in {"header", header_block.section} for link in links)

    draft = await service.get_page_draft(page.id)
    await service.save_page_draft(
        page_id=page.id,
        payload={"blocks": []},
        meta={"globalBlocks": {}},
        comment=None,
        review_status=PageReviewStatus.NONE,
        expected_version=draft.version,
        actor="editor@example.com",
    )
    links_after = await service.list_page_global_blocks(page.id)
    assert links_after == []


@pytest.mark.asyncio()
async def test_save_page_draft_duplicate_ids_fails(service: SiteService):
    page = await service.create_page(
        slug="/duplicate",
        page_type=PageType.LANDING,
        title="Duplicate test",
        locale="ru",
        owner=None,
    )
    draft = await service.get_page_draft(page.id)
    assert draft.version == 1

    with pytest.raises(SiteValidationError) as exc_info:
        await service.save_page_draft(
            page_id=page.id,
            payload={
                "blocks": [
                    {"id": "hero-1", "type": "hero", "enabled": True},
                    {"id": "hero-1", "type": "hero", "enabled": True},
                ]
            },
            meta={},
            comment=None,
            review_status=PageReviewStatus.NONE,
            expected_version=draft.version,
            actor=None,
        )
    error = exc_info.value
    assert error.code == "site_page_validation_failed"
    assert "hero-1" in error.block_errors
    assert error.block_errors["hero-1"]
    assert error.general_errors


@pytest.mark.asyncio()
async def test_draft_save_publish_and_history(service: SiteService):
    page = await service.create_page(
        slug="/home",
        page_type=PageType.LANDING,
        title="Home",
        locale="en",
        owner=None,
    )
    draft = await service.get_page_draft(page.id)
    assert draft.version == 1

    updated = await service.save_page_draft(
        page_id=page.id,
        payload={
            "blocks": [
                {"id": "hero-1", "type": "hero", "enabled": True},
            ]
        },
        meta={"title": "Home"},
        comment="init",
        review_status=PageReviewStatus.PENDING,
        expected_version=draft.version,
        actor="user@example.com",
    )
    assert updated.version == 2
    assert updated.review_status == PageReviewStatus.PENDING

    published = await service.publish_page(
        page_id=page.id,
        actor="user@example.com",
        comment="release",
        diff=None,
    )
    assert published.version == 1
    assert published.diff is not None
    assert any(entry.get("change") == "added" for entry in published.diff or [])

    history, total = await service.list_page_history(page.id)
    assert total == 1
    assert history[0].comment == "release"
    assert history[0].diff is not None


@pytest.mark.asyncio()
async def test_publish_page_generates_diff_and_audit(service: SiteService):
    page = await service.create_page(
        slug="/diff",
        page_type=PageType.LANDING,
        title="Diff test",
        locale="ru",
        owner="marketing",
        actor="creator@example.com",
    )
    initial_draft = await service.get_page_draft(page.id)
    await service.save_page_draft(
        page_id=page.id,
        payload={
            "blocks": [
                {
                    "id": "hero-1",
                    "type": "hero",
                    "enabled": True,
                    "title": "Hero Block",
                },
                {
                    "id": "cta-1",
                    "type": "custom_carousel",
                    "enabled": True,
                    "title": "CTA",
                },
            ]
        },
        meta={"title": "Diff test"},
        comment="seed",
        review_status=PageReviewStatus.NONE,
        expected_version=initial_draft.version,
        actor="editor@example.com",
    )
    first_version = await service.publish_page(
        page_id=page.id,
        actor="publisher@example.com",
        comment="first release",
        diff=None,
    )
    assert any(entry.get("change") == "added" for entry in first_version.diff or [])

    draft_after_publish = await service.get_page_draft(page.id)
    await service.save_page_draft(
        page_id=page.id,
        payload={
            "blocks": [
                {
                    "id": "hero-1",
                    "type": "hero",
                    "enabled": True,
                    "title": "Hero Block Updated",
                },
                {
                    "id": "promo-1",
                    "type": "recommendations",
                    "enabled": True,
                    "title": "Promo",
                },
            ]
        },
        meta={"title": "Diff test v2"},
        comment="second iteration",
        review_status=PageReviewStatus.PENDING,
        expected_version=draft_after_publish.version,
        actor="editor@example.com",
    )
    second_version = await service.publish_page(
        page_id=page.id,
        actor="publisher@example.com",
        comment="second release",
        diff=None,
    )
    assert second_version.version == 2
    assert second_version.diff
    diff_signatures = {
        (
            entry.get("type"),
            entry.get("blockId") or entry.get("field"),
            entry.get("change"),
        )
        for entry in second_version.diff or []
    }
    assert ("block", "hero-1", "updated") in diff_signatures
    assert ("block", "cta-1", "removed") in diff_signatures
    assert ("block", "promo-1", "added") in diff_signatures
    assert ("meta", "title", "updated") in diff_signatures

    history, total = await service.list_page_history(page.id)
    assert total == 2
    assert history[0].version == 2
    assert history[0].diff is not None

    audit_rows, _ = await service.list_audit(entity_type="page", entity_id=page.id)
    actions = {row["action"] for row in audit_rows}
    assert {"create", "draft_save", "publish"} <= actions
    publish_snapshot = _snapshot_to_dict(
        next(row["snapshot"] for row in audit_rows if row["action"] == "publish")
    )
    assert publish_snapshot.get("diff")
    publish_diff_signatures = {
        (
            entry.get("type"),
            entry.get("blockId") or entry.get("field"),
            entry.get("change"),
        )
        for entry in publish_snapshot.get("diff") or []
    }
    assert ("block", "promo-1", "added") in publish_diff_signatures


@pytest.mark.asyncio()
async def test_diff_page_draft(service: SiteService):
    page = await service.create_page(
        slug="/diff-preview",
        page_type=PageType.LANDING,
        title="Diff preview",
        locale="ru",
        owner="marketing",
    )
    initial = await service.get_page_draft(page.id)
    await service.save_page_draft(
        page_id=page.id,
        payload={
            "blocks": [
                {"id": "hero-1", "type": "hero", "enabled": True, "title": "Hero"},
                {
                    "id": "items-1",
                    "type": "nodes_carousel",
                    "enabled": True,
                    "title": "Nodes",
                },
            ]
        },
        meta={"title": "First"},
        comment=None,
        review_status=PageReviewStatus.NONE,
        expected_version=initial.version,
        actor="author@example.com",
    )
    await service.publish_page(
        page_id=page.id,
        actor="publisher@example.com",
        comment="initial",
        diff=None,
    )
    draft_after = await service.get_page_draft(page.id)
    new_draft = await service.save_page_draft(
        page_id=page.id,
        payload={
            "blocks": [
                {
                    "id": "hero-1",
                    "type": "hero",
                    "enabled": True,
                    "title": "Hero Updated",
                },
                {
                    "id": "promo-1",
                    "type": "recommendations",
                    "enabled": True,
                    "title": "Promo",
                },
            ]
        },
        meta={"title": "Second"},
        comment=None,
        review_status=PageReviewStatus.PENDING,
        expected_version=draft_after.version,
        actor="author@example.com",
    )
    diff, draft_version, published_version = await service.diff_page_draft(page.id)
    assert draft_version == new_draft.version
    assert published_version == 1
    signatures = {
        (
            entry.get("type"),
            entry.get("blockId") or entry.get("field"),
            entry.get("change"),
        )
        for entry in diff
    }
    assert ("block", "hero-1", "updated") in signatures
    assert ("block", "items-1", "removed") in signatures
    assert ("block", "promo-1", "added") in signatures
    assert ("meta", "title", "updated") in signatures


@pytest.mark.asyncio()
async def test_restore_version_creates_new_draft(service: SiteService):
    page = await service.create_page(
        slug="/about",
        page_type=PageType.LANDING,
        title="About",
        locale="ru",
        owner=None,
    )
    initial = await service.get_page_draft(page.id)
    await service.save_page_draft(
        page_id=page.id,
        payload={"blocks": [{"id": "hero", "type": "hero", "enabled": True}]},
        meta={},
        comment=None,
        review_status=PageReviewStatus.NONE,
        expected_version=initial.version,
        actor=None,
    )
    await service.publish_page(
        page_id=page.id,
        actor=None,
        comment=None,
        diff=None,
    )

    restored = await service.restore_page_version(page.id, 1, actor="editor")
    assert restored.version >= 2
    assert restored.data["blocks"][0]["id"] == "hero"
    audit_rows, _ = await service.list_audit(entity_type="page", entity_id=page.id)
    actions = {row["action"] for row in audit_rows}
    assert "restore" in actions


@pytest.mark.asyncio()
async def test_global_block_lifecycle(service: SiteService, notify_stub):
    block = await service.create_global_block(
        key="header-default",
        title="Header",
        section="header",
        locale="ru",
        requires_publisher=True,
        data={"links": []},
        meta={},
    )
    assert block.status == GlobalBlockStatus.DRAFT
    assert block.section == "header"
    assert block.requires_publisher is True

    saved = await service.save_global_block(
        block_id=block.id,
        payload={"links": [{"title": "Home", "href": "/"}]},
        meta={},
        version=block.draft_version,
        comment="draft comment",
        review_status=PageReviewStatus.PENDING,
        actor="editor@example.com",
    )
    assert saved.draft_version and saved.draft_version >= 2
    assert saved.review_status == PageReviewStatus.PENDING
    assert saved.comment == "draft comment"

    published, audit_id, usage_after, jobs = await service.publish_global_block(
        block_id=block.id,
        actor="publisher@example.com",
        comment="initial",
        diff=None,
    )
    assert audit_id
    assert published.status == GlobalBlockStatus.PUBLISHED
    assert published.review_status == PageReviewStatus.NONE
    assert published.comment == "initial"
    assert usage_after == []
    assert jobs == []

    audit_rows, total = await service.list_audit(
        entity_type="global_block", entity_id=block.id
    )
    assert total >= 3
    actions = {row["action"] for row in audit_rows}
    assert {"create", "update", "publish"} <= actions
    publish_snapshot = _snapshot_to_dict(
        next(row["snapshot"] for row in audit_rows if row["action"] == "publish")
    )
    assert publish_snapshot.get("diff")
    assert publish_snapshot.get("usage") == []
    assert notify_stub.commands == []


@pytest.mark.asyncio()
async def test_publish_global_block_notifies_page_owner(
    service: SiteService, notify_stub
):
    block = await service.create_global_block(
        key="header-shared",
        title="Shared Header",
        section="header",
        locale="ru",
        requires_publisher=False,
        data={},
        meta={},
    )
    page = await service.create_page(
        slug="/owner-page",
        page_type=PageType.LANDING,
        title="Owner Page",
        locale="ru",
        owner="marketing",
        actor="creator@example.com",
    )
    await service.save_page_draft(
        page_id=page.id,
        payload={"blocks": []},
        meta={
            "globalBlocks": [
                {
                    "type": "global_block",
                    "reference": block.key,
                    "section": "header",
                }
            ]
        },
        expected_version=page.draft_version or 1,
        comment=None,
        review_status=PageReviewStatus.NONE,
        actor="editor@example.com",
    )

    published, audit_id, usage_after, _ = await service.publish_global_block(
        block_id=block.id,
        actor="publisher@example.com",
        comment="notify owners",
        diff=None,
    )

    assert published.status == GlobalBlockStatus.PUBLISHED
    assert usage_after and usage_after[0].owner == "marketing"
    assert notify_stub.commands
    command = notify_stub.commands[0]
    assert command.user_id == "marketing"
    assert command.meta["block_id"] == str(block.id)
    pages_meta = command.meta["pages"]
    assert any(entry["slug"] == "/owner-page" for entry in pages_meta)

    audit_rows, _ = await service.list_audit(
        entity_type="global_block", entity_id=block.id
    )
    publish_snapshot = _snapshot_to_dict(
        next(row["snapshot"] for row in audit_rows if row["action"] == "publish")
    )
    assert any(item["slug"] == "/owner-page" for item in publish_snapshot["usage"])


@pytest.mark.asyncio()
async def test_list_global_blocks_filters(service: SiteService):
    block_requires_pub = await service.create_global_block(
        key="nav-main",
        title="Main Nav",
        section="header",
        locale="ru",
        requires_publisher=True,
        data={},
        meta={},
    )
    await service.save_global_block(
        block_id=block_requires_pub.id,
        payload={},
        meta={},
        version=block_requires_pub.draft_version,
        comment=None,
        review_status=PageReviewStatus.PENDING,
        actor="editor@example.com",
    )
    await service.create_global_block(
        key="promo-banner",
        title="Promo",
        section="promo",
        locale="en",
        requires_publisher=False,
        data={},
        meta={},
    )

    filtered_requires_pub, total_requires = await service.list_global_blocks(
        requires_publisher=True
    )
    assert total_requires >= 1
    assert any(item.requires_publisher for item in filtered_requires_pub)
    assert any(item.key == "nav-main" for item in filtered_requires_pub)

    filtered_review_status, total_review = await service.list_global_blocks(
        review_status=PageReviewStatus.PENDING
    )
    assert total_review >= 1
    assert any(
        item.review_status == PageReviewStatus.PENDING
        for item in filtered_review_status
    )
    assert any(item.key == "nav-main" for item in filtered_review_status)

    filtered_no_pub, total_no_pub = await service.list_global_blocks(
        requires_publisher=False
    )
    assert total_no_pub >= 1
    assert any(not item.requires_publisher for item in filtered_no_pub)
    assert any(item.key == "promo-banner" for item in filtered_no_pub)


@pytest.mark.asyncio()
async def test_global_block_history_and_restore(service: SiteService):
    block = await service.create_global_block(
        key="footer-default",
        title="Footer",
        section="footer",
        locale="en",
        requires_publisher=False,
        data={"columns": []},
        meta={},
    )
    await service.save_global_block(
        block_id=block.id,
        payload={"columns": [{"title": "Links"}]},
        meta={},
        version=block.draft_version,
        comment="draft v1",
        review_status=PageReviewStatus.NONE,
        actor="editor@example.com",
    )
    first_block, _, _, _ = await service.publish_global_block(
        block_id=block.id,
        actor="publisher@example.com",
        comment="publish v1",
        diff=None,
    )
    assert first_block.published_version == 1

    second_draft = await service.save_global_block(
        block_id=block.id,
        payload={"columns": [{"title": "Links"}, {"title": "Contacts"}]},
        meta={},
        version=first_block.draft_version,
        comment="draft v2",
        review_status=PageReviewStatus.PENDING,
        actor="editor@example.com",
    )
    second_block, _, _, _ = await service.publish_global_block(
        block_id=block.id,
        actor="publisher@example.com",
        comment="publish v2",
        diff=None,
    )
    assert second_block.published_version == 2

    history, total = await service.list_global_block_history(
        block.id, limit=10, offset=0
    )
    assert total == 2
    assert history[0].version == 2
    assert history[1].version == 1
    version_one = await service.get_global_block_version(block.id, 1)
    assert version_one.comment == "publish v1"

    restored_block = await service.restore_global_block_version(
        block.id, 1, actor="restorer@example.com"
    )
    assert restored_block.draft_version == (second_draft.draft_version or 0) + 1
    assert restored_block.comment == "Restore version 1"
    assert restored_block.review_status == PageReviewStatus.NONE

    audit_rows, _ = await service.list_audit(
        entity_type="global_block", entity_id=block.id
    )
    actions = {row["action"] for row in audit_rows}
    assert "restore" in actions


@pytest.mark.asyncio()
async def test_list_pages_respects_viewer_access(service: SiteService):
    marketing_published = await service.create_page(
        slug="/marketing-published",
        page_type=PageType.LANDING,
        title="Marketing Published",
        locale="ru",
        owner="marketing",
    )
    await service.publish_page(
        page_id=marketing_published.id,
        actor="publisher@example.com",
        comment=None,
        diff=None,
    )

    await service.create_page(
        slug="/marketing-draft",
        page_type=PageType.LANDING,
        title="Marketing Draft",
        locale="ru",
        owner="marketing",
    )

    await service.create_page(
        slug="/team-draft",
        page_type=PageType.LANDING,
        title="Team Draft",
        locale="ru",
        owner="team-beta",
    )

    team_published = await service.create_page(
        slug="/team-published",
        page_type=PageType.LANDING,
        title="Team Published",
        locale="ru",
        owner="team-beta",
    )
    await service.publish_page(
        page_id=team_published.id,
        actor="publisher@example.com",
        comment=None,
        diff=None,
    )

    restricted_pages, restricted_total = await service.list_pages(
        viewer_roles=set(),
        viewer_team="team-beta",
        viewer_id="user-beta",
        sort="title_asc",
        page_size=20,
    )
    restricted_slugs = {page.slug for page in restricted_pages}
    assert "/marketing-published" in restricted_slugs
    assert "/team-published" in restricted_slugs
    assert "/team-draft" in restricted_slugs
    assert "/marketing-draft" not in restricted_slugs
    assert restricted_total == len(restricted_slugs)

    elevated_pages, _ = await service.list_pages(
        viewer_roles={"editor"},
        sort="title_asc",
        page_size=20,
    )
    elevated_slugs = {page.slug for page in elevated_pages}
    assert {
        "/marketing-published",
        "/marketing-draft",
        "/team-draft",
        "/team-published",
    } <= elevated_slugs
