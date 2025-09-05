#!/usr/bin/env python
"""
Генератор тестовых данных для базы.

Пример запуска:
  python scripts/seed_db.py --wipe --users 5 --nodes 30 --transitions 60 --echoes 100
  python scripts/seed_db.py --users 2 --nodes 5 --no-embeddings

Параметры читаются из .env через Settings.
"""
import argparse
import asyncio
import logging
import random
import string
from datetime import datetime, timedelta

from apps.backend.app.core.config import settings
from apps.backend.app.core.security import get_password_hash
from apps.backend.app.domains.ai.application.embedding_service import (
    update_node_embedding,
)
from apps.backend.app.domains.navigation.infrastructure.models import (
    transition_models as tm,
)
from apps.backend.app.domains.navigation.infrastructure.models.echo_models import (
    EchoTrace,
)
from apps.backend.app.domains.nodes.infrastructure.models.node import Node
from apps.backend.app.domains.users.infrastructure.models.user import User
from apps.backend.app.providers.db.session import (
    create_tables,
    db_session,
    init_db,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def rand_username(prefix: str = "user") -> string:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}_{suffix}"


def rand_title() -> str:
    words = [
        "Sky",
        "Ocean",
        "Forest",
        "Mountain",
        "River",
        "City",
        "Dream",
        "Echo",
        "Light",
        "Shadow",
    ]
    return " ".join(random.choices(words, k=random.randint(2, 4)))


def rand_tags() -> list[str]:
    pool = [
        "story",
        "tech",
        "art",
        "music",
        "travel",
        "food",
        "premium",
        "news",
        "science",
        "fun",
    ]
    k = random.randint(0, 4)
    return random.sample(pool, k=k)


async def wipe_db(session: AsyncSession) -> None:
    """Очищает таблицы (в порядке зависимостей)."""
    logger.info("Wiping existing data...")
    # Безопасное удаление по порядку (TRUNCATE CASCADE можно,
    # но делаем кросс-совместимо)
    for table in (
        "echo_trace",
        "node_transitions",
        "node_moderation",
        "user_restrictions",
        "nodes",
        "users",
    ):
        await session.execute(text(f"DELETE FROM {table};"))
    await session.commit()
    logger.info("Data wiped.")


async def create_users(session: AsyncSession, count: int) -> list[User]:
    users: list[User] = []
    for _i in range(count):
        username = rand_username()
        email = f"{username}@example.com"
        is_premium = random.random() < 0.3
        premium_until = None
        if is_premium:
            premium_until = datetime.utcnow() + timedelta(days=random.randint(7, 60))

        u = User(
            email=email,
            username=username,
            password_hash=get_password_hash("password123"),
            is_active=True,
            is_premium=is_premium,
            premium_until=premium_until,
            role="user",
            bio=None,
            avatar_url=None,
        )
        session.add(u)
        users.append(u)

    # Добавим одного админа
    admin = User(
        email="admin@example.com",
        username="admin",
        password_hash=get_password_hash("admin123"),
        is_active=True,
        is_premium=True,
        premium_until=datetime.utcnow() + timedelta(days=365),
        role="admin",
    )
    session.add(admin)
    users.append(admin)

    await session.commit()
    # refresh ids
    for u in users:
        await session.refresh(u)
    logger.info("Created %d users (+1 admin)", count)
    return users


async def create_nodes(
    session: AsyncSession, authors: list[User], count: int, compute_embeddings: bool
) -> list[Node]:
    nodes: list[Node] = []
    for i in range(count):
        author = random.choice(authors)
        title = rand_title()
        content = {"text": f"# {title}\n\nThis is a generated content block #{i}."}
        media = []
        tags = rand_tags()
        is_public = random.random() < 0.8
        is_visible = True
        premium_only = "premium" in tags and random.random() < 0.5

        n = Node(
            title=title,
            content=content,
            media=media,
            tags=tags,
            author_id=author.id,
            is_public=is_public,
            is_visible=is_visible,
            premium_only=premium_only,
            ai_generated=True,
        )
        session.add(n)
        nodes.append(n)

    await session.commit()
    for n in nodes:
        await session.refresh(n)

    if compute_embeddings:
        logger.info("Computing embeddings for %d nodes...", len(nodes))
        for n in nodes:
            await update_node_embedding(session, n)
        logger.info("Embeddings computed.")

    logger.info("Created %d nodes", len(nodes))
    return nodes


async def create_transitions(
    session: AsyncSession, nodes: list[Node], users: list[User], count: int
) -> list[tm.NodeTransition]:
    if len(nodes) < 2:
        return []
    transitions: list[tm.NodeTransition] = []
    pairs = set()
    max_attempts = count * 3
    attempts = 0
    while len(transitions) < count and attempts < max_attempts:
        attempts += 1
        frm, to = random.sample(nodes, 2)
        key = (str(frm.id), str(to.id))
        if key in pairs:
            continue
        pairs.add(key)
        t = tm.NodeTransition(
            from_node_id=frm.id,
            to_node_id=to.id,
            type=tm.NodeTransitionType.manual,
            condition={},
            weight=random.randint(1, 5),
            label=random.choice(["Open", "Read more", "Next", "Explore"]),
            created_by=random.choice(users).id,
        )
        session.add(t)
        transitions.append(t)

    await session.commit()
    for t in transitions:
        await session.refresh(t)
    logger.info("Created %d transitions", len(transitions))
    return transitions


async def create_echo_traces(
    session: AsyncSession, nodes: list[Node], users: list[User], count: int
) -> None:
    if len(nodes) < 2:
        return
    for _ in range(count):
        frm, to = random.sample(nodes, 2)
        user = random.choice(users + [None])  # иногда анонимно
        trace = EchoTrace(
            from_node_id=frm.id,
            to_node_id=to.id,
            user_id=(user.id if isinstance(user, User) and user.is_premium else None),
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 29)),
        )
        session.add(trace)
    await session.commit()
    logger.info("Created %d echo traces", count)


async def main():
    parser = argparse.ArgumentParser(description="Seed database with sample data")
    parser.add_argument(
        "--users", type=int, default=5, help="Количество пользователей (кроме админа)"
    )
    parser.add_argument("--nodes", type=int, default=30, help="Количество узлов")
    parser.add_argument("--transitions", type=int, default=60, help="Количество переходов")
    parser.add_argument("--echoes", type=int, default=100, help="Количество echo-трасс")
    parser.add_argument("--wipe", action="store_true", help="Очистить базу перед заполнением")
    parser.add_argument(
        "--no-embeddings", action="store_true", help="Не считать эмбеддинги для узлов"
    )
    args = parser.parse_args()

    logger.info("Seeding database for environment: %s", settings.env_mode)

    # Применяем миграции, затем гарантируем создание всех таблиц из моделей
    await init_db()
    await create_tables()

    async with db_session() as session:
        if args.wipe:
            await wipe_db(session)

        users = await create_users(session, args.users)
        nodes = await create_nodes(
            session, users, args.nodes, compute_embeddings=not args.no_embeddings
        )
        await create_transitions(session, nodes, users, args.transitions)
        await create_echo_traces(session, nodes, users, args.echoes)

    logger.info("Seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
