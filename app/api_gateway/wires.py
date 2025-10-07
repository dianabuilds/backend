from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from domains.platform.events.adapters.event_bus_memory import InMemoryEventBus
from domains.platform.events.adapters.outbox_memory import InMemoryOutbox
from packages.core import Flags
from packages.core.config import Settings, load_settings, to_async_dsn
from packages.core.testing import is_test_mode

from .container_registry import container_registry

try:
    import redis.asyncio as aioredis  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - optional dependency
    aioredis = None  # type: ignore[assignment]

"""DI wiring for DDD app: only DDD imports, no monolith references."""


logger = logging.getLogger(__name__)


# Platform dependencies
build_admin_container = container_registry.resolve("platform.admin.build_container")
build_audit_container = container_registry.resolve("platform.audit.build_container")
build_billing_container = container_registry.resolve("platform.billing.build_container")
RedisEventBus = container_registry.resolve("platform.events.RedisEventBus")
ProfileOutboxRedis = container_registry.resolve("platform.events.RedisOutbox")
Events = container_registry.resolve("platform.events.Events")
build_flags_container = container_registry.resolve("platform.flags.build_container")
build_iam_container = container_registry.resolve("platform.iam.build_container")
build_media_container = container_registry.resolve("platform.media.build_container")
build_platform_moderation_container = container_registry.resolve(
    "platform.moderation.build_container"
)
register_email_channel = container_registry.resolve(
    "platform.notifications.register_email_channel"
)
register_webhook_channel = container_registry.resolve(
    "platform.notifications.register_webhook_channel"
)
build_notifications_container = container_registry.resolve(
    "platform.notifications.build_container"
)
register_event_relays = container_registry.resolve(
    "platform.notifications.register_event_relays"
)
build_quota_container = container_registry.resolve("platform.quota.build_container")
build_search_container = container_registry.resolve("platform.search.build_container")
register_event_indexers = container_registry.resolve(
    "platform.search.register_event_indexers"
)
build_telemetry_container = container_registry.resolve(
    "platform.telemetry.build_container"
)
build_users_container = container_registry.resolve("platform.users.build_container")

# Product dependencies
ProfileIamClient = container_registry.resolve("product.profile.IamClient")
ProfileRepoFactory = container_registry.resolve("product.profile.SQLRepo")
ProfileService = container_registry.resolve("product.profile.Service")
TagsRepoFactory = container_registry.resolve("product.tags.SQLRepo")
TagUsageStore = container_registry.resolve("product.tags.TagUsageStore")
register_tags_usage_writer = container_registry.resolve(
    "product.tags.register_usage_writer"
)
SQLTagCatalog = container_registry.resolve("product.tags.SQLTagCatalog")
TagService = container_registry.resolve("product.tags.TagService")

NodesRepoFactory = container_registry.resolve("product.nodes.SQLRepo")
NodeViewsRepoFactory = container_registry.resolve("product.nodes.SQLNodeViewsRepo")
NodeReactionsRepoFactory = container_registry.resolve(
    "product.nodes.SQLNodeReactionsRepo"
)
NodeCommentsRepoFactory = container_registry.resolve(
    "product.nodes.SQLNodeCommentsRepo"
)
RedisNodeViewLimiter = container_registry.resolve("product.nodes.RedisNodeViewLimiter")
MemoryTagCatalog = container_registry.resolve("product.nodes.MemoryTagCatalog")
MemoryUsageProjection = container_registry.resolve(
    "product.nodes.MemoryUsageProjection"
)
UsageProjectionFactory = container_registry.resolve("product.nodes.SQLUsageProjection")
EmbeddingClient = container_registry.resolve("product.nodes.EmbeddingClient")
register_embedding_worker = container_registry.resolve(
    "product.nodes.register_embedding_worker"
)
NodeViewsService = container_registry.resolve("product.nodes.NodeViewsService")
NodeReactionsService = container_registry.resolve("product.nodes.NodeReactionsService")
NodeCommentsService = container_registry.resolve("product.nodes.NodeCommentsService")
NodesService = container_registry.resolve("product.nodes.NodeService")

_ = container_registry.resolve(
    "product.navigation.NodesPort"
)  # ensure navigation ports are imported
NavigationService = container_registry.resolve("product.navigation.NavigationService")

if TYPE_CHECKING:
    from domains.product.navigation.application.ports import (
        NodesPort as NavigationNodesPort,
    )
else:
    NavigationNodesPort = Any  # type: ignore[assignment]

LLMRegistryFactory = container_registry.resolve("product.ai.LLMRegistry")
AIRegistryProvider = container_registry.resolve("product.ai.RegistryProvider")
AIFakeProvider = container_registry.resolve("product.ai.FakeProvider")
AIService = container_registry.resolve("product.ai.AIService")

AchievementsRepoFactory = container_registry.resolve("product.achievements.SQLRepo")
DddAchievementsService = container_registry.resolve("product.achievements.Service")
DddAchievementsAdminService = container_registry.resolve(
    "product.achievements.AdminService"
)

WorldsRepoFactory = container_registry.resolve("product.worlds.SQLRepo")
DddWorldsService = container_registry.resolve("product.worlds.Service")

ReferralsRepoFactory = container_registry.resolve("product.referrals.SQLRepo")
DddReferralsService = container_registry.resolve("product.referrals.Service")

DddPremiumService = container_registry.resolve("product.premium.Service")

QuestsRepoFactory = container_registry.resolve("product.quests.SQLRepo")
QuestsService = container_registry.resolve("product.quests.Service")

ModerationRepoFactory = container_registry.resolve("product.moderation.SQLRepo")
DddModerationService = container_registry.resolve("product.moderation.Service")


# Simple reachability check to decide SQL vs Memory repos
def _db_reachable(url: str, *, allow_remote: bool = False) -> bool:
    try:
        import socket
        from urllib.parse import urlparse

        u = urlparse(url)
        host = u.hostname or "localhost"
        port = u.port or 5432
        with socket.create_connection((host, port), timeout=0.25):
            return True
    except OSError:
        return False


def _require_async_dsn(settings: Settings, *, allow_remote: bool) -> str:
    dsn = to_async_dsn(settings.database_url)
    if not dsn:
        raise RuntimeError("APP_DATABASE_URL is required for SQL-backed storages")
    if not _db_reachable(str(settings.database_url), allow_remote=allow_remote):
        raise RuntimeError("database unreachable for SQL-backed storages")
    return dsn


@dataclass
class Container:
    settings: Settings
    events: Any
    profile_service: Any
    nodes_service: Any
    tags_service: Any
    quests_service: Any
    navigation_service: Any
    ai_service: Any | None
    ai_registry: Any
    achievements_service: Any
    achievements_admin: Any
    worlds_service: Any
    referrals_service: Any
    referrals_repo: Any
    premium_service: Any
    moderation_service: Any
    telemetry: Any
    quota: Any
    iam: Any
    search: Any
    platform_moderation: Any
    media: Any
    audit: Any
    billing: Any
    flags: Any
    notifications: Any
    users: Any
    admin: Any


def build_container(env: str = "dev") -> Container:
    # Configuration is provided via pydantic-settings
    settings = load_settings()
    test_mode = is_test_mode(settings)
    allow_remote_db = bool(
        getattr(settings, "database_allow_remote", False) or settings.env == "prod"
    )
    try:
        dsn_primary = _require_async_dsn(settings, allow_remote=allow_remote_db)
    except RuntimeError as exc:
        logger.info("Primary database unavailable; using in-memory fallbacks: %s", exc)
        dsn_primary = None

    # Events wiring: Redis is required in all environments
    topics = [t.strip() for t in str(settings.event_topics).split(",") if t.strip()]
    if "node.embedding.requested.v1" not in topics:
        topics.append("node.embedding.requested.v1")
    if test_mode:
        outbox = InMemoryOutbox()
        bus = InMemoryEventBus()
    else:
        try:
            import redis  # type: ignore
            from redis.exceptions import RedisError as SyncRedisError  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Redis is required for platform events; ensure APP_REDIS_URL is installed"
            ) from exc

        try:
            rc = redis.Redis.from_url(str(settings.redis_url), decode_responses=True)
            rc.ping()
        except SyncRedisError as exc:
            raise RuntimeError(
                "Redis is required for platform events; ensure APP_REDIS_URL is reachable"
            ) from exc
        finally:
            try:
                rc.close()
            except Exception:
                logger.debug(
                    "Failed to close Redis connection during wiring", exc_info=True
                )
        outbox = ProfileOutboxRedis(str(settings.redis_url))
        bus = RedisEventBus(
            redis_url=str(settings.redis_url),
            topics=topics,
            group=str(settings.event_group),
        )
    events = Events(outbox=outbox, bus=bus)

    profile_iam = ProfileIamClient()
    profile_repo = ProfileRepoFactory(settings)
    svc = ProfileService(
        repo=profile_repo, outbox=outbox, iam=profile_iam, flags=Flags()
    )

    nodes_repo = NodesRepoFactory(settings)
    node_views_repo = NodeViewsRepoFactory(settings)
    node_reactions_repo = NodeReactionsRepoFactory(settings)
    node_comments_repo = NodeCommentsRepoFactory(settings)

    node_views_limiter = None
    if not test_mode and aioredis is not None and settings.redis_url:
        try:
            node_views_limiter_client = aioredis.from_url(
                str(settings.redis_url), decode_responses=False
            )
            node_views_limiter = RedisNodeViewLimiter(
                node_views_limiter_client, per_day=True
            )
        except Exception as exc:
            logger.warning("Failed to initialize node view limiter: %s", exc)
            node_views_limiter = None

    node_views_service = NodeViewsService(node_views_repo, limiter=node_views_limiter)
    node_reactions_service = NodeReactionsService(node_reactions_repo)
    node_comments_service = NodeCommentsService(node_comments_repo)
    outbox_bridge = outbox  # unify events outbox across services

    if dsn_primary:
        try:
            tag_catalog = SQLTagCatalog(dsn_primary)
        except Exception as exc:
            logger.warning("Falling back to in-memory tag catalog: %s", exc)
            tag_catalog = MemoryTagCatalog()
    else:
        logger.debug("Tag catalog: using in-memory backend (no SQL DSN available)")
        tag_catalog = MemoryTagCatalog()

    tag_usage_store = TagUsageStore()
    usage_proj = UsageProjectionFactory(
        settings,
        store=tag_usage_store,
        content_type="node",
    )

    embedding_client = EmbeddingClient(
        base_url=settings.embedding_api_base,
        model=settings.embedding_model,
        api_key=settings.embedding_api_key,
        provider=settings.embedding_provider,
        timeout=settings.embedding_timeout,
        connect_timeout=settings.embedding_connect_timeout,
        retries=settings.embedding_retries,
        enabled=settings.embedding_enabled,
    )
    nodes = NodesService(
        repo=nodes_repo,
        tags=tag_catalog,
        outbox=outbox_bridge,
        usage=usage_proj,
        embedding=embedding_client,
        views=node_views_service,
        reactions=node_reactions_service,
        comments=node_comments_service,
    )
    register_embedding_worker(events, nodes)

    # Tags service based on usage store
    tags_repo = TagsRepoFactory(settings, store=tag_usage_store)
    tags = TagService(tags_repo)

    # Quests
    quests_repo = QuestsRepoFactory(settings)
    quests = QuestsService(repo=quests_repo, tags=tag_catalog, outbox=outbox_bridge)

    # Navigation (depends on nodes service read port)
    class _NodesReadPort:
        def list_by_author(self, author_id: str, *, limit: int = 50, offset: int = 0):
            items = nodes.list_by_author(author_id, limit=limit, offset=offset)
            return [
                {
                    "id": it.id,
                    "author_id": it.author_id,
                    "title": it.title,
                    "tags": list(it.tags),
                    "embedding": (
                        list(it.embedding) if it.embedding is not None else None
                    ),
                    "is_public": it.is_public,
                }
                for it in items
            ]

        def get(self, node_id: int):
            v = nodes.get(node_id)
            return (
                {
                    "id": v.id,
                    "author_id": v.author_id,
                    "title": v.title,
                    "tags": list(v.tags),
                    "embedding": list(v.embedding) if v.embedding is not None else None,
                    "is_public": v.is_public,
                }
                if v
                else None
            )

        def search_by_embedding(
            self, embedding: Sequence[float], *, limit: int = 64
        ) -> Sequence[dict]:
            items = nodes.search_by_embedding(embedding, limit=limit)
            return [
                {
                    "id": it.id,
                    "author_id": it.author_id,
                    "title": it.title,
                    "tags": list(it.tags),
                    "embedding": (
                        list(it.embedding) if it.embedding is not None else None
                    ),
                    "is_public": it.is_public,
                }
                for it in items
            ]

    navigation_port = _NodesReadPort()
    navigation = NavigationService(nodes=cast(NavigationNodesPort, navigation_port))

    # AI (sql-backed registry)
    ai_registry = LLMRegistryFactory(settings, dsn=dsn_primary)
    ai_provider = AIRegistryProvider(ai_registry, fallback=AIFakeProvider())
    ai = AIService(provider=ai_provider, outbox=outbox_bridge)

    # Achievements
    ach_repo = AchievementsRepoFactory(settings)
    achievements_service = DddAchievementsService(ach_repo, outbox=outbox)
    achievements_admin = DddAchievementsAdminService(ach_repo, outbox=outbox)

    # Worlds
    worlds_repo = WorldsRepoFactory(settings)
    worlds_service = DddWorldsService(worlds_repo, outbox=outbox)

    # Referrals
    referrals_repo = ReferralsRepoFactory(settings)
    referrals_service = DddReferralsService(referrals_repo, outbox=outbox)

    # Premium
    premium_service = DddPremiumService()

    # Moderation
    _mod_repo = ModerationRepoFactory(settings)
    moderation_service = DddModerationService(_mod_repo, outbox=outbox)
    telemetry = build_telemetry_container(settings)
    quota = build_quota_container(settings)
    # Wire notifications: channels + event subscriptions
    if settings.notify_webhook_url:
        register_webhook_channel(str(settings.notify_webhook_url))
    # Email channel (mock by default)
    register_email_channel(settings)
    notify_topics = [
        t.strip()
        for t in str(settings.notify_topics or settings.event_topics).split(",")
        if t.strip()
    ]
    iam_container = build_iam_container(settings)
    search = build_search_container()
    # Index incoming events into search
    register_event_indexers(events, search)
    # Tags usage writer (optional; only if DB available)
    if dsn_primary:
        try:
            register_tags_usage_writer(events, dsn_primary)
        except Exception as exc:
            logger.warning("Failed to register tags usage writer: %s", exc)
    media = build_media_container()
    platform_moderation = build_platform_moderation_container(settings)
    audit = build_audit_container()
    billing = build_billing_container(settings)
    flags = build_flags_container(settings)
    notifications = build_notifications_container(settings, flag_service=flags.service)
    try:
        notify_loop = asyncio.get_running_loop()
    except RuntimeError:
        notify_loop = None
    register_event_relays(
        events, notify_topics, delivery=notifications.delivery, loop=notify_loop
    )
    users = build_users_container(settings)
    admin = build_admin_container(settings)
    return Container(
        settings=settings,
        events=events,
        profile_service=svc,
        nodes_service=nodes,
        tags_service=tags,
        quests_service=quests,
        navigation_service=navigation,
        ai_service=ai,
        ai_registry=ai_registry,
        achievements_service=achievements_service,
        achievements_admin=achievements_admin,
        worlds_service=worlds_service,
        referrals_service=referrals_service,
        referrals_repo=referrals_repo,
        premium_service=premium_service,
        moderation_service=moderation_service,
        telemetry=telemetry,
        quota=quota,
        iam=iam_container,
        search=search,
        platform_moderation=platform_moderation,
        media=media,
        audit=audit,
        billing=billing,
        flags=flags,
        notifications=notifications,
        users=users,
        admin=admin,
    )
