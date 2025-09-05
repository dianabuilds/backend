from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.navigation.application.compass_service import CompassService
from app.domains.navigation.application.echo_service import EchoService
from app.domains.navigation.application.random_service import RandomService
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User


class ModesService:
    def __init__(self) -> None:
        self._compass = CompassService()
        self._echo = EchoService()
        self._random = RandomService()

    async def apply_mode(
        self,
        db: AsyncSession,
        node: Node,
        user: User,
        *,
        mode: str,
        max_options: int,
        tag_whitelist: list[str] | None = None,
    ) -> list[dict]:
        if mode == "compass":
            nodes = await self._compass.get_compass_nodes(db, node, user, max_options)
            return [{"slug": n.slug, "label": n.title, "mode": mode} for n in nodes]
        if mode == "echo":
            nodes = await self._echo.get_echo_transitions(db, node, max_options, user=user)
            return [{"slug": n.slug, "label": n.title, "mode": mode} for n in nodes]
        if mode == "random":
            options: list[dict] = []
            for _ in range(max_options):
                rnd = await self._random.get_random_node(
                    db,
                    user=user,
                    exclude_node_id=str(node.id),
                    tag_whitelist=tag_whitelist,
                )
                if not rnd:
                    break
                if rnd.slug in {o["slug"] for o in options}:
                    continue
                options.append({"slug": rnd.slug, "label": rnd.title, "mode": mode})
                if len(options) >= max_options:
                    break
            return options
        return []
