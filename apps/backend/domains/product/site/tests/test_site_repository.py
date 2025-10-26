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

    pages, total = await service.list_pages()
    assert total == 1
    assert pages[0].slug == "/"


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
                {"id": "hero-1", "type": "hero", "enabled": True, "title": "Hero Block"},
                {"id": "cta-1", "type": "custom_carousel", "enabled": True, "title": "CTA"},
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
                {"id": "promo-1", "type": "recommendations", "enabled": True, "title": "Promo"},
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
        (entry.get("type"), entry.get("blockId") or entry.get("field"), entry.get("change"))
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
        (entry.get("type"), entry.get("blockId") or entry.get("field"), entry.get("change"))
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
                {"id": "items-1", "type": "nodes_carousel", "enabled": True, "title": "Nodes"},
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
                {"id": "hero-1", "type": "hero", "enabled": True, "title": "Hero Updated"},
                {"id": "promo-1", "type": "recommendations", "enabled": True, "title": "Promo"},
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
        (entry.get("type"), entry.get("blockId") or entry.get("field"), entry.get("change"))
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
async def test_global_block_lifecycle(service: SiteService):
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

    audit_rows, total = await service.list_audit(entity_type="global_block", entity_id=block.id)
    assert total >= 3
    actions = {row["action"] for row in audit_rows}
    assert {"create", "update", "publish"} <= actions
    publish_snapshot = _snapshot_to_dict(
        next(row["snapshot"] for row in audit_rows if row["action"] == "publish")
    )
    assert publish_snapshot.get("diff")


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

    history, total = await service.list_global_block_history(block.id, limit=10, offset=0)
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

    audit_rows, _ = await service.list_audit(entity_type="global_block", entity_id=block.id)
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
        viewer_roles={"site.editor"},
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
