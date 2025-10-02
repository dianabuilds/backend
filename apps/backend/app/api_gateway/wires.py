from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass

from domains.platform.admin.wires import AdminContainer
from domains.platform.admin.wires import build_container as build_admin_container
from domains.platform.audit.wires import AuditContainer
from domains.platform.audit.wires import build_container as build_audit_container
from domains.platform.billing.wires import BillingContainer
from domains.platform.billing.wires import build_container as build_billing_container
from domains.platform.events.adapters.event_bus_redis import RedisEventBus
from domains.platform.events.adapters.outbox_redis import (
    RedisOutbox as ProfileOutboxRedis,
)
from domains.platform.events.service import Events
from domains.platform.flags.wires import FlagsContainer
from domains.platform.flags.wires import build_container as build_flags_container
from domains.platform.iam.wires import IAMContainer
from domains.platform.iam.wires import build_container as build_iam_container
from domains.platform.media.wires import MediaContainer
from domains.platform.media.wires import build_container as build_media_container
from domains.platform.moderation.wires import (
    ModerationContainer as PlatformModerationContainer,
)
from domains.platform.moderation.wires import (
    build_container as build_platform_moderation_container,
)
from domains.platform.notifications.adapters.email_smtp import register_email_channel
from domains.platform.notifications.adapters.webhook import register_webhook_channel
from domains.platform.notifications.wires import (
    NotificationsContainer,
    register_event_relays,
)
from domains.platform.notifications.wires import (
    build_container as build_notifications_container,
)
from domains.platform.quota.wires import QuotaContainer
from domains.platform.quota.wires import build_container as build_quota_container
from domains.platform.search.wires import SearchContainer, register_event_indexers
from domains.platform.search.wires import build_container as build_search_container
from domains.platform.telemetry.wires import TelemetryContainer
from domains.platform.telemetry.wires import (
    build_container as build_telemetry_container,
)
from domains.platform.users.wires import UsersContainer
from domains.platform.users.wires import build_container as build_users_container
from domains.product.profile.adapters.iam_client import (
    IamClient as ProfileIamClient,
)
from domains.product.profile.adapters.repo_sql import SQLProfileRepo
from domains.product.profile.application.ports import (
    IamClient as ProfileIam,
)
from domains.product.profile.application.ports import (
    Outbox as ProfileOutbox,
)
from domains.product.profile.application.ports import (
    Repo as ProfileRepo,
)
from domains.product.profile.application.services import (
    Service as ProfileService,
)
from domains.product.referrals.application.ports import Repo as ReferralsRepo
from domains.product.tags.adapters.repo_sql import SQLTagsRepo
from domains.product.tags.adapters.store_memory import TagUsageStore
from domains.product.tags.adapters.usage_sql_writer import (
    register_tags_usage_writer,
)
from packages.core import Flags
from packages.core.config import Settings, load_settings, to_async_dsn

"""DI wiring for DDD app: only DDD imports, no monolith references."""


logger = logging.getLogger(__name__)


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


# Product domain services
from domains.product.achievements.adapters.repo_sql import (
    SQLRepo as AchievementsSQLRepo,
)
from domains.product.achievements.application.service import (
    AchievementsAdminService as DddAchievementsAdminService,
)
from domains.product.achievements.application.service import (
    AchievementsService as DddAchievementsService,
)
from domains.product.ai.adapters.provider_fake import FakeProvider as AIFakeProvider
from domains.product.ai.adapters.provider_registry import (
    RegistryBackedProvider as AIRegistryProvider,
)
from domains.product.ai.application.registry import LLMRegistry
from domains.product.ai.application.service import AIService
from domains.product.moderation.adapters.repo_sql import SQLModerationRepo
from domains.product.moderation.application.service import (
    ModerationService as DddModerationService,
)
from domains.product.navigation.application.ports import (
    NodesPort as _NodesPort,
)
from domains.product.navigation.application.service import (
    NavigationService as NavigationService,
)
from domains.product.nodes.adapters.repo_sql import SQLNodesRepo
from domains.product.nodes.adapters.tag_catalog_memory import MemoryTagCatalog
from domains.product.nodes.adapters.usage_memory import MemoryUsageProjection
from domains.product.nodes.adapters.usage_sql import SQLUsageProjection
from domains.product.nodes.application.embedding import EmbeddingClient
from domains.product.nodes.application.embedding_worker import register_embedding_worker
from domains.product.nodes.application.ports import (
    TagCatalog as NodesTagCatalog,
)
from domains.product.nodes.application.ports import (
    UsageProjection as NodesUsageProjection,
)
from domains.product.nodes.application.service import NodeService as NodesService
from domains.product.premium.application.service import (
    PremiumService as DddPremiumService,
)
from domains.product.quests.adapters.repo_sql import SQLQuestsRepo
from domains.product.quests.application.service import QuestService as QuestsService
from domains.product.referrals.adapters.repo_sql import SQLReferralsRepo
from domains.product.referrals.application.service import (
    ReferralsService as DddReferralsService,
)
from domains.product.tags.adapters.tag_catalog_sql import SQLTagCatalog
from domains.product.tags.application.service import TagService as TagsService
from domains.product.worlds.adapters.repo_sql import SQLWorldsRepo
from domains.product.worlds.application.service import WorldsService as DddWorldsService


@dataclass
class Container:
    settings: Settings
    events: Events
    profile_service: ProfileService
    # Product services
    nodes_service: NodesService
    tags_service: TagsService
    quests_service: QuestsService
    navigation_service: NavigationService
    ai_service: AIService | None
    ai_registry: LLMRegistry
    achievements_service: DddAchievementsService
    achievements_admin: DddAchievementsAdminService
    worlds_service: DddWorldsService
    referrals_service: DddReferralsService
    referrals_repo: ReferralsRepo
    premium_service: DddPremiumService
    moderation_service: DddModerationService
    telemetry: TelemetryContainer
    quota: QuotaContainer
    iam: IAMContainer
    search: SearchContainer
    platform_moderation: PlatformModerationContainer
    media: MediaContainer
    audit: AuditContainer
    billing: BillingContainer
    flags: FlagsContainer
    notifications: NotificationsContainer
    users: UsersContainer
    admin: AdminContainer


def build_container(env: str = "dev") -> Container:
    # Configuration is provided via pydantic-settings
    settings = load_settings()
    allow_remote_db = bool(
        getattr(settings, "database_allow_remote", False) or settings.env == "prod"
    )
    dsn_primary = _require_async_dsn(settings, allow_remote=allow_remote_db)

    # Events wiring: Redis is required in all environments
    topics = [t.strip() for t in str(settings.event_topics).split(",") if t.strip()]
    if "node.embedding.requested.v1" not in topics:
        topics.append("node.embedding.requested.v1")
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
    outbox: ProfileOutbox = ProfileOutboxRedis(str(settings.redis_url))
    bus = RedisEventBus(
        redis_url=str(settings.redis_url),
        topics=topics,
        group=str(settings.event_group),
    )
    events = Events(outbox=outbox, bus=bus)
    profile_iam: ProfileIam = ProfileIamClient()
    profile_repo: ProfileRepo = SQLProfileRepo(dsn_primary)
    svc = ProfileService(
        repo=profile_repo, outbox=outbox, iam=profile_iam, flags=Flags()
    )

    # --- Product domains wiring (DDD-only) ---
    # Nodes / tags helpers
    nodes_repo = SQLNodesRepo(dsn_primary)
    outbox_bridge = outbox  # unify events outbox across services
    tag_catalog: NodesTagCatalog
    try:
        tag_catalog = SQLTagCatalog(dsn_primary)
    except Exception as exc:
        logger.warning("Falling back to in-memory tag catalog: %s", exc)
        tag_catalog = MemoryTagCatalog()
    usage_proj: NodesUsageProjection
    try:
        usage_proj = SQLUsageProjection(dsn_primary, content_type="node")
    except Exception as exc:
        logger.warning("Falling back to in-memory usage projection: %s", exc)
        usage_proj = MemoryUsageProjection(TagUsageStore(), content_type="node")
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
    )
    register_embedding_worker(events, nodes)

    # Tags service based on usage store
    tags_repo = SQLTagsRepo(dsn_primary)
    tags = TagsService(tags_repo)

    # Quests
    quests_repo = SQLQuestsRepo(dsn_primary)
    quests = QuestsService(repo=quests_repo, tags=tag_catalog, outbox=outbox_bridge)

    # Navigation (depends on nodes service read port)
    class _NodesReadPort(_NodesPort):  # type: ignore[misc]
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

    navigation = NavigationService(nodes=_NodesReadPort())

    # AI (sql-backed registry)
    ai_registry = LLMRegistry(dsn_primary)
    ai_provider = AIRegistryProvider(ai_registry, fallback=AIFakeProvider())
    ai = AIService(provider=ai_provider, outbox=outbox_bridge)

    # Achievements
    ach_repo = AchievementsSQLRepo(dsn_primary)
    achievements_service = DddAchievementsService(ach_repo, outbox=outbox)
    achievements_admin = DddAchievementsAdminService(ach_repo, outbox=outbox)

    # Worlds
    worlds_repo = SQLWorldsRepo(dsn_primary)
    worlds_service = DddWorldsService(worlds_repo, outbox=outbox)

    # Referrals
    referrals_repo = SQLReferralsRepo(dsn_primary)
    referrals_service = DddReferralsService(referrals_repo, outbox=outbox)

    # Premium
    premium_service = DddPremiumService()

    # Moderation
    _mod_repo = SQLModerationRepo(dsn_primary)
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
    try:
        from packages.core.config import to_async_dsn as _to_async

        dsn = _to_async(settings.database_url)
        if dsn:
            register_tags_usage_writer(events, dsn)
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
        # Product services
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
