from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, Dict, List, Mapping, Sequence

import pytest
from fastapi import HTTPException

from domains.product.nodes.application.use_cases.catalog_mutations import (
    CatalogMutationsService,
)
from domains.product.nodes.application.use_cases.engagement import (
    EngagementService,
)
from domains.product.nodes.application.use_cases.comments import CommentsService
from domains.product.nodes.application.use_cases.ports import NodesServicePort
from domains.product.nodes.domain.results import NodeView
from domains.product.nodes.application.ports import (
    NodeCommentBanDTO,
    NodeCommentDTO,
    NodeReactionsSummary,
    NodeViewStat,
)
from domains.product.nodes.utils import normalize_actor_id


AUTHOR_ID = normalize_actor_id({"sub": "author-1"})


class StubNodeService(NodesServicePort):
    def __init__(self) -> None:
        self.views: Dict[int, NodeView] = {
            1: NodeView(
                id=1,
                slug="node-1",
                author_id=AUTHOR_ID,
                title="Title",
                tags=["init"],
                is_public=True,
                status="published",
            )
        }
        self.next_node_id = 2
        self.deleted_nodes: set[int] = set()
        self.view_total: Dict[int, int] = {1: 0}
        self.view_stats: Dict[int, List[NodeViewStat]] = {
            1: [NodeViewStat(node_id=1, bucket_date="2025-01-01", views=3)]
        }
        self.likes: Dict[int, set[str]] = {1: set()}
        self.comments: Dict[int, NodeCommentDTO] = {
            10: NodeCommentDTO(
                id=10,
                node_id=1,
                author_id=AUTHOR_ID,
                parent_comment_id=None,
                depth=0,
                content="hello",
                status="published",
                metadata={},
                created_at="2025-01-01",
                updated_at="2025-01-01",
            )
        }
        self.comment_bans: Dict[int, Dict[str, NodeCommentBanDTO]] = {1: {}}
        self.next_comment_id = 11
        self.events: Dict[str, Any] = {}

    async def update_tags(
        self, node_id: int, new_slugs: Sequence[str], *, actor_id: str
    ) -> NodeView:
        view = self.views[node_id]
        updated = replace(view, tags=list(new_slugs))
        self.views[node_id] = updated
        return updated

    async def create(
        self,
        *,
        author_id: str,
        title: str | None,
        tags: Sequence[str] | None,
        is_public: bool,
        status: str | None = None,
        publish_at: str | None = None,
        unpublish_at: str | None = None,
        content_html: str | None = None,
        cover_url: str | None = None,
    ) -> NodeView:
        node_id = self.next_node_id
        self.next_node_id += 1
        view = NodeView(
            id=node_id,
            slug=f"node-{node_id}",
            author_id=author_id,
            title=title,
            tags=list(tags or []),
            is_public=is_public,
            status=status,
            publish_at=publish_at,
            unpublish_at=unpublish_at,
            content_html=content_html,
            cover_url=cover_url,
        )
        self.views[node_id] = view
        self.view_total[node_id] = 0
        self.likes[node_id] = set()
        self.comment_bans.setdefault(node_id, {})
        return view

    async def update(
        self,
        node_id: int,
        *,
        title: str | None = None,
        is_public: bool | None = None,
        status: str | None = None,
        publish_at: str | None = None,
        unpublish_at: str | None = None,
        content_html: str | None = None,
        cover_url: str | None = None,
    ) -> NodeView:
        view = self.views[node_id]
        updated = replace(
            view,
            title=view.title if title is None else title,
            is_public=view.is_public if is_public is None else is_public,
            status=view.status if status is None else status,
            publish_at=view.publish_at if publish_at is None else publish_at,
            unpublish_at=view.unpublish_at if unpublish_at is None else unpublish_at,
            content_html=view.content_html if content_html is None else content_html,
            cover_url=view.cover_url if cover_url is None else cover_url,
        )
        self.views[node_id] = updated
        return updated

    async def delete(self, node_id: int) -> bool:
        self.deleted_nodes.add(node_id)
        return True

    async def register_view(
        self,
        node_id: int,
        *,
        viewer_id: str | None = None,
        fingerprint: str | None = None,
        amount: int = 1,
        at: datetime | None = None,
    ) -> int:
        self.view_total[node_id] = self.view_total.get(node_id, 0) + amount
        return self.view_total[node_id]

    async def get_total_views(self, node_id: int) -> int:
        return self.view_total.get(node_id, 0)

    async def get_view_stats(
        self, node_id: int, *, limit: int = 30, offset: int = 0
    ) -> list[NodeViewStat]:
        return self.view_stats.get(node_id, [])

    async def add_like(self, node_id: int, *, user_id: str) -> bool:
        liked = user_id not in self.likes.setdefault(node_id, set())
        self.likes[node_id].add(user_id)
        return liked

    async def remove_like(self, node_id: int, *, user_id: str) -> bool:
        removed = user_id in self.likes.setdefault(node_id, set())
        self.likes[node_id].discard(user_id)
        return removed

    async def get_reactions_summary(
        self, node_id: int, *, user_id: str | None = None
    ) -> NodeReactionsSummary:
        likes = self.likes.setdefault(node_id, set())
        user_reaction = "like" if user_id and user_id in likes else None
        return NodeReactionsSummary(
            node_id=node_id,
            totals={"like": len(likes)} if likes else {},
            user_reaction=user_reaction,
        )

    async def list_comments(
        self,
        node_id: int,
        *,
        parent_comment_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> list[NodeCommentDTO]:
        comments = [c for c in self.comments.values() if c.node_id == node_id]
        if not include_deleted:
            comments = [c for c in comments if c.status != "deleted"]
        return comments

    async def create_comment(
        self,
        *,
        node_id: int,
        author_id: str,
        content: str,
        parent_comment_id: int | None = None,
        metadata: dict | None = None,
    ) -> NodeCommentDTO:
        comment_id = self.next_comment_id
        self.next_comment_id += 1
        comment = NodeCommentDTO(
            id=comment_id,
            node_id=node_id,
            author_id=author_id,
            parent_comment_id=parent_comment_id,
            depth=0,
            content=content,
            status="published",
            metadata=dict(metadata or {}),
            created_at="2025-01-01",
            updated_at="2025-01-01",
        )
        self.comments[comment_id] = comment
        return comment

    async def get_comment(self, comment_id: int) -> NodeCommentDTO | None:
        return self.comments.get(comment_id)

    async def delete_comment(
        self,
        comment_id: int,
        *,
        actor_id: str,
        hard: bool = False,
        reason: str | None = None,
    ) -> bool:
        comment = self.comments.get(comment_id)
        if comment is None:
            return False
        if hard:
            self.comments.pop(comment_id, None)
            return True
        self.comments[comment_id] = replace(comment, status="deleted")
        return True

    async def update_comment_status(
        self,
        comment_id: int,
        *,
        status: str,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> NodeCommentDTO:
        comment = self.comments[comment_id]
        updated = replace(comment, status=status)
        self.comments[comment_id] = updated
        return updated

    async def lock_comments(
        self, node_id: int, *, actor_id: str, reason: str | None = None
    ) -> None:
        view = self.views[node_id]
        self.views[node_id] = replace(
            view,
            comments_locked_by=actor_id,
            comments_locked_at=datetime.now(UTC).isoformat(),
        )

    async def unlock_comments(
        self, node_id: int, *, actor_id: str | None = None
    ) -> None:
        view = self.views[node_id]
        self.views[node_id] = replace(
            view,
            comments_locked_by=None,
            comments_locked_at=None,
        )

    async def disable_comments(
        self,
        node_id: int,
        *,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> None:
        self.views[node_id] = replace(self.views[node_id], comments_disabled=True)

    async def enable_comments(
        self,
        node_id: int,
        *,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> None:
        self.views[node_id] = replace(self.views[node_id], comments_disabled=False)

    async def ban_comment_user(
        self,
        node_id: int,
        target_user_id: str,
        *,
        actor_id: str,
        reason: str | None = None,
    ) -> NodeCommentBanDTO:
        ban = NodeCommentBanDTO(
            node_id=node_id,
            target_user_id=target_user_id,
            set_by=actor_id,
            reason=reason,
            created_at="2025-01-01",
        )
        self.comment_bans.setdefault(node_id, {})[target_user_id] = ban
        return ban

    async def unban_comment_user(self, node_id: int, target_user_id: str) -> bool:
        return self.comment_bans.get(node_id, {}).pop(target_user_id, None) is not None

    async def list_comment_bans(self, node_id: int) -> list[NodeCommentBanDTO]:
        return list(self.comment_bans.get(node_id, {}).values())

    async def _repo_get_async(self, node_id: int):
        return self.views.get(node_id)

    async def _repo_get_by_slug_async(self, slug: str):
        for view in self.views.values():
            if view.slug == slug:
                return view
        return None

    def _to_view(self, dto):
        return dto


def _claims(sub: str | None = None, role: str | None = None) -> Mapping[str, Any]:
    payload: Dict[str, Any] = {}
    if sub is not None:
        payload["sub"] = sub
    if role is not None:
        payload["role"] = role
    return payload


@pytest.fixture()
def service() -> StubNodeService:
    return StubNodeService()


class TestCatalogMutationsService:
    @pytest.mark.asyncio
    async def test_set_tags_requires_author(self, service: StubNodeService):
        catalog = CatalogMutationsService(nodes_service=service)
        with pytest.raises(HTTPException) as exc:
            await catalog.set_tags("1", ["a"], None)
        assert exc.value.status_code == 401

        with pytest.raises(HTTPException) as exc:
            await catalog.set_tags("1", ["a"], _claims(sub="intruder"))
        assert exc.value.status_code == 403

        result = await catalog.set_tags("1", ["foo"], _claims(sub=AUTHOR_ID))
        assert result["tags"] == ["foo"]

    @pytest.mark.asyncio
    async def test_create_node_uses_actor(self, service: StubNodeService):
        catalog = CatalogMutationsService(nodes_service=service)
        body = {"title": "New", "tags": ["x"], "is_public": True}
        result = await catalog.create(body, _claims(sub="author-2"))
        assert result["id"] == 2
        assert result["tags"] == ["x"]

    @pytest.mark.asyncio
    async def test_update_changes_fields(self, service: StubNodeService):
        catalog = CatalogMutationsService(nodes_service=service)
        result = await catalog.update("1", {"title": "Updated"}, _claims(sub=AUTHOR_ID))
        assert result["title"] == "Updated"


class _FakeSavedViewsRepo:
    def __init__(self) -> None:
        self.storage: Dict[str, Dict[str, dict]] = {}
        self.calls: list[str] = []

    async def list_for_user(self, user_id: str):
        self.calls.append("list")
        return [
            SimpleNamespace(
                name="default", config={"filters": {}}, is_default=True, updated_at=None
            )
        ]

    async def upsert(
        self, user_id: str, *, name: str, config: dict, is_default: bool
    ) -> None:
        self.calls.append("upsert")
        self.storage.setdefault(user_id, {})[name] = {
            "config": config,
            "is_default": is_default,
        }

    async def delete(self, user_id: str, name: str) -> None:
        self.calls.append("delete")
        self.storage.get(user_id, {}).pop(name, None)

    async def set_default(self, user_id: str, name: str) -> None:
        self.calls.append("set_default")
        for record in self.storage.setdefault(user_id, {}).values():
            record["is_default"] = False
        self.storage[user_id][name] = {"config": {}, "is_default": True}


class TestEngagementService:
    @pytest.mark.asyncio
    async def test_register_view_invalid_amount(self, service: StubNodeService):
        engagement = EngagementService(nodes_service=service)
        with pytest.raises(HTTPException) as exc:
            await engagement.register_view(
                "1", {"amount": "bad"}, _claims(sub="viewer")
            )
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_register_view_success(self, service: StubNodeService):
        engagement = EngagementService(nodes_service=service)
        result = await engagement.register_view(
            "1", {"amount": 2}, _claims(sub="viewer")
        )
        assert result == {"id": 1, "views_count": 2}

    @pytest.mark.asyncio
    async def test_add_like_requires_actor(self, service: StubNodeService):
        engagement = EngagementService(nodes_service=service)
        with pytest.raises(HTTPException) as exc:
            await engagement.add_like("1", None)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_add_like_success(self, service: StubNodeService):
        engagement = EngagementService(nodes_service=service)
        response = await engagement.add_like("1", _claims(sub="user-1"))
        assert response["liked"] is True
        assert response["summary"]["totals"] == {"like": 1}

    @pytest.mark.asyncio
    async def test_saved_view_validation(self, service: StubNodeService):
        repo = _FakeSavedViewsRepo()
        engagement = EngagementService(nodes_service=service, saved_views=repo)
        with pytest.raises(HTTPException) as exc:
            await engagement.upsert_saved_view(
                {"name": "test", "config": []}, _claims(sub="user-1")
            )
        assert exc.value.status_code == 400

        result = await engagement.upsert_saved_view(
            {"name": "test", "config": {"filters": {}}, "is_default": True},
            _claims(sub="user-1"),
        )
        assert result == {"ok": True}
        assert "upsert" in repo.calls


class TestCommentsService:
    @pytest.mark.asyncio
    async def test_list_comments_requires_permission(self, service: StubNodeService):
        comments = CommentsService(nodes_service=service)
        with pytest.raises(HTTPException) as exc:
            await comments.list_comments(
                "1",
                parent_comment_id=None,
                limit=50,
                offset=0,
                include_deleted=True,
                claims=_claims(sub="other"),
            )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_create_comment_validates_content(self, service: StubNodeService):
        comments = CommentsService(nodes_service=service)
        with pytest.raises(HTTPException) as exc:
            await comments.create_comment("1", {"content": ""}, _claims(sub=AUTHOR_ID))
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_comment_forbidden(self, service: StubNodeService):
        comments = CommentsService(nodes_service=service)
        with pytest.raises(HTTPException) as exc:
            await comments.delete_comment(
                10,
                hard=False,
                reason=None,
                claims=_claims(sub="intruder"),
            )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_update_comment_status_requires_moderator(
        self, service: StubNodeService
    ):
        comments = CommentsService(nodes_service=service)
        with pytest.raises(HTTPException) as exc:
            await comments.update_comment_status(
                10, {"status": "hidden"}, _claims(sub=AUTHOR_ID)
            )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_toggle_lock_by_author(self, service: StubNodeService):
        comments = CommentsService(nodes_service=service)
        result = await comments.toggle_comments_lock(
            "1",
            {"locked": True},
            _claims(sub=AUTHOR_ID),
        )
        assert result["locked"] is True
        assert service.views[1].comments_locked_by == AUTHOR_ID

        result = await comments.toggle_comments_lock(
            "1",
            {"locked": False},
            _claims(sub=AUTHOR_ID),
        )
        assert result["locked"] is False
        assert service.views[1].comments_locked_by is None
