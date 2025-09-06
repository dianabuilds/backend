from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.audit.application.audit_service import audit_log
from app.domains.nodes.application.ports.node_repo_port import INodeRepository
from app.domains.nodes.infrastructure.models.feedback import Feedback
from app.domains.notifications.application.notify_service import NotifyService


class FeedbackService:
    def __init__(self, repo: INodeRepository, notifier: NotifyService | None = None) -> None:
        self._repo = repo
        self._notifier = notifier

    async def list_feedback(
        self, db: AsyncSession, slug: str, current_user, workspace_id: int
    ) -> list[Feedback]:
        node = await self._repo.get_by_slug(slug, workspace_id)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        if not node.allow_feedback and node.author_id != current_user.id:
            raise HTTPException(status_code=403, detail="Feedback disabled")
        result = await db.execute(
            select(Feedback).where(Feedback.node_id == node.id, Feedback.is_hidden.is_(False))
        )
        return result.scalars().all()

    async def create_feedback(
        self,
        db: AsyncSession,
        slug: str,
        content: dict,
        is_anonymous: bool,
        current_user,
        workspace_id: int,
    ) -> Feedback:
        if (
            not isinstance(content, dict)
            or "text" not in content
            or not str(content["text"]).strip()
        ):
            raise HTTPException(status_code=400, detail="Empty feedback")
        node = await self._repo.get_by_slug(slug, workspace_id)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        if not node.allow_feedback:
            raise HTTPException(status_code=403, detail="Feedback disabled")
        if not node.is_visible and node.author_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to comment on this node")
        feedback = Feedback(
            node_id=node.id,
            author_id=current_user.id,
            content=content,
            is_anonymous=is_anonymous,
        )
        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)

        # Уведомление автора узла
        try:
            if self._notifier and node.author_id != current_user.id:
                await self._notifier.create_notification(
                    user_id=node.author_id,
                    account_id=workspace_id,
                    title="New feedback",
                    message=str(content.get("text") or "New feedback"),
                    type=None,
                )
        except Exception:
            pass

        # Аудит
        try:
            await audit_log(
                db,
                actor_id=str(current_user.id),
                action="node_feedback_create",
                resource_type="node",
                resource_id=str(node.id),
                after={"feedback_id": str(feedback.id)},
            )
        except Exception:
            pass

        return feedback

    async def delete_feedback(
        self,
        db: AsyncSession,
        slug: str,
        feedback_id: UUID,
        current_user,
        workspace_id: int,
    ) -> dict:
        node = await self._repo.get_by_slug(slug, workspace_id)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        result = await db.execute(
            select(Feedback).where(Feedback.id == feedback_id, Feedback.node_id == node.id)
        )
        feedback = result.scalars().first()
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        if current_user.id not in (node.author_id, feedback.author_id):
            raise HTTPException(status_code=403, detail="Not authorized")
        feedback.is_hidden = True
        await db.commit()

        try:
            await audit_log(
                db,
                actor_id=str(current_user.id),
                action="node_feedback_delete",
                resource_type="node",
                resource_id=str(node.id),
                before={"feedback_id": str(feedback_id)},
            )
        except Exception:
            pass

        return {"status": "ok"}
