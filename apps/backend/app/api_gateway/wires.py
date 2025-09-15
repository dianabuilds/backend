from __future__ import annotations

from dataclasses import dataclass

from domains.platform.audit.wires import AuditContainer
from domains.platform.audit.wires import build_container as build_audit_container
from domains.platform.billing.wires import BillingContainer
from domains.platform.billing.wires import build_container as build_billing_container
from domains.platform.events.adapters.event_bus_memory import InMemoryEventBus
from domains.platform.events.adapters.event_bus_redis import RedisEventBus
from domains.platform.events.adapters.outbox_memory import (
    MemoryOutbox as EventsMemoryOutbox,
)
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
from domains.product.profile.adapters.repo_memory import (
    MemoryRepo as ProfileRepoMemory,
)
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

from domains.product.profile.adapters.repo_sql import SQLProfileRepo
from domains.product.tags.adapters.repo_sql import SQLTagsRepo
from domains.product.tags.adapters.usage_sql_writer import (
    register_tags_usage_writer,
)
from packages.core.config import Settings, load_settings
from packages.core import Flags

"""DI wiring for DDD app: only DDD imports, no monolith references."""

# Simple reachability check to decide SQL vs Memory repos
def _db_reachable(url: str) -> bool:
    try:
        from urllib.parse import urlparse
        import socket

        u = urlparse(url)
        host = u.hostname or "localhost"
        port = u.port or 5432
        with socket.create_connection((host, port), timeout=0.25):
            return True
    except Exception:
        return False

# Product domain services
from domains.product.achievements.adapters.repo_memory import (
    MemoryRepo as AchievementsMemoryRepo,
)
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
from domains.product.ai.application.service import AIService
from domains.product.moderation.adapters.repo_memory import MemoryModerationRepo
from domains.product.moderation.application.service import (
    ModerationService as DddModerationService,
)
from domains.product.navigation.application.service import (
    NavigationService as NavigationService,
)
from domains.product.nodes.adapters.repo_memory import MemoryNodesRepo
from domains.product.nodes.adapters.tag_catalog_memory import MemoryTagCatalog
from domains.product.nodes.adapters.usage_memory import MemoryUsageProjection
from domains.product.nodes.application.service import NodeService as NodesService
from domains.product.premium.application.service import (
    PremiumService as DddPremiumService,
)
from domains.product.quests.adapters.repo_memory import MemoryQuestsRepo
from domains.product.quests.application.service import QuestService as QuestsService
from domains.product.referrals.adapters.repo_memory import MemoryReferralsRepo
from domains.product.referrals.application.service import (
    ReferralsService as DddReferralsService,
)
from domains.product.tags.adapters.repo_memory import MemoryTagsRepo
from domains.product.tags.adapters.store_memory import TagUsageStore
from domains.product.tags.application.service import TagService as TagsService
from domains.product.worlds.adapters.repo_memory import MemoryRepo as WorldsMemoryRepo
from domains.product.worlds.application.service import WorldsService as DddWorldsService

from domains.product.worlds.adapters.repo_sql import SQLWorldsRepo
from domains.product.moderation.adapters.repo_sql import SQLModerationRepo
from domains.product.referrals.adapters.repo_sql import SQLReferralsRepo
from domains.product.navigation.application.ports import (
    NodesPort as _NodesPort,
)
from domains.product.nodes.adapters.repo_sql import SQLNodesRepo
from domains.product.quests.adapters.repo_sql import SQLQuestsRepo


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
    achievements_service: DddAchievementsService
    achievements_admin: DddAchievementsAdminService
    worlds_service: DddWorldsService
    referrals_service: DddReferralsService
    referrals_repo: MemoryReferralsRepo
    premium_service: DddPremiumService
    moderation_service: DddModerationService
    telemetry: TelemetryContainer
    quota: QuotaContainer
    iam: IAMContainer
    search: SearchContainer
    media: MediaContainer
    audit: AuditContainer
    billing: BillingContainer
    flags: FlagsContainer
    notifications: NotificationsContainer
    users: UsersContainer


def build_container(env: str = "dev") -> Container:
    # Configuration is provided via pydantic-settings
    settings = load_settings()
    repo: ProfileRepo = ProfileRepoMemory()
    # Events wiring: Redis mandatory in prod, optional in dev/test
    topics = [t.strip() for t in str(settings.event_topics).split(",") if t.strip()]
    if settings.env == "prod":
        try:
            import redis  # type: ignore

            rc = redis.Redis.from_url(str(settings.redis_url), decode_responses=True)
            rc.ping()
        except Exception as e:
            raise RuntimeError("Redis is required for events/outbox in prod") from e
        outbox: ProfileOutbox = ProfileOutboxRedis(str(settings.redis_url))
        bus = RedisEventBus(
            redis_url=str(settings.redis_url), topics=topics, group=str(settings.event_group)
        )
    else:
        try:
            import redis  # type: ignore

            rc = redis.Redis.from_url(str(settings.redis_url), decode_responses=True)
            rc.ping()
            outbox = ProfileOutboxRedis(str(settings.redis_url))
            bus = RedisEventBus(
                redis_url=str(settings.redis_url), topics=topics, group=str(settings.event_group)
            )
        except Exception:
            # no Redis available -> in-memory bus, and a no-op outbox via memory
            outbox = EventsMemoryOutbox()  # type: ignore[assignment]
            bus = InMemoryEventBus()
    events = Events(outbox=outbox, bus=bus)
    iam: ProfileIam = ProfileIamClient()
    svc = ProfileService(repo=repo, outbox=outbox, iam=iam, flags=Flags())

    # Try SQL repo for Profile if DB reachable (no event-loop gymnastics)
    try:
        dsn = str(settings.database_url)
        if _db_reachable(dsn):
            svc = ProfileService(
                repo=SQLProfileRepo(dsn), outbox=outbox, iam=iam, flags=Flags()
            )
    except Exception:
        pass

    # --- Product domains wiring (DDD-only) ---
    # Shared tag usage store
    tag_usage = TagUsageStore()
    # Nodes
    nodes_repo = MemoryNodesRepo()
    tag_catalog = MemoryTagCatalog()
    outbox_bridge = outbox  # unify events outbox across services
    usage_proj = MemoryUsageProjection(tag_usage, content_type="node")
    # Prefer SQL repo when DB is reachable
    try:
        from packages.core.config import to_async_dsn as _to_async

        _dsn_nodes = _to_async(settings.database_url)
        if _dsn_nodes and _db_reachable(str(settings.database_url)):
            nodes_repo = SQLNodesRepo(_dsn_nodes)  # type: ignore[assignment]
    except Exception:
        pass
    nodes = NodesService(
        repo=nodes_repo, tags=tag_catalog, outbox=outbox_bridge, usage=usage_proj
    )

    # Tags service based on usage store
    tags_repo = MemoryTagsRepo(tag_usage)
    try:
        from packages.core.config import to_async_dsn as _to_async

        dsn_tags = _to_async(settings.database_url)
        if dsn_tags and _db_reachable(str(settings.database_url)):
            # Switch to SQL-backed read repo while keeping usage writer
            tags_repo = SQLTagsRepo(dsn_tags)  # type: ignore[assignment]
    except Exception:
        pass
    tags = TagsService(tags_repo)

    # Quests
    quests_repo = MemoryQuestsRepo()
    try:
        from packages.core.config import to_async_dsn as _to_async

        dsn_q = _to_async(settings.database_url)
        if dsn_q and _db_reachable(str(settings.database_url)):
            quests_repo = SQLQuestsRepo(dsn_q)  # type: ignore[assignment]
    except Exception:
        pass
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
                    "is_public": v.is_public,
                }
                if v
                else None
            )

    navigation = NavigationService(nodes=_NodesReadPort())

    # AI (dev default provider)
    ai = AIService(provider=AIFakeProvider(), outbox=outbox_bridge)

    # Achievements
    ach_repo = AchievementsMemoryRepo()
    try:
        from packages.core.config import to_async_dsn as _to_async

        dsn_ach = _to_async(settings.database_url)
        if dsn_ach and (_db_reachable(str(settings.database_url))):
            ach_repo = AchievementsSQLRepo(dsn_ach)  # type: ignore[assignment]
    except Exception:
        pass
    achievements_service = DddAchievementsService(ach_repo, outbox=outbox)
    achievements_admin = DddAchievementsAdminService(ach_repo, outbox=outbox)

    # Worlds
    worlds_repo = WorldsMemoryRepo()
    try:
        from packages.core.config import to_async_dsn as _to_async

        dsn_worlds = _to_async(settings.database_url)
        if dsn_worlds and _db_reachable(str(settings.database_url)):
            worlds_repo = SQLWorldsRepo(dsn_worlds)  # type: ignore[assignment]
    except Exception:
        pass
    worlds_service = DddWorldsService(worlds_repo, outbox=outbox)

    # Referrals
    referrals_repo = MemoryReferralsRepo()
    try:
        from packages.core.config import to_async_dsn as _to_async

        dsn_ref = _to_async(settings.database_url)
        if dsn_ref and _db_reachable(str(settings.database_url)):
            referrals_repo = SQLReferralsRepo(dsn_ref)  # type: ignore[assignment]
    except Exception:
        pass
    referrals_service = DddReferralsService(referrals_repo, outbox=outbox)

    # Premium
    premium_service = DddPremiumService()

    # Moderation
    _mod_repo = MemoryModerationRepo()
    try:
        from packages.core.config import to_async_dsn as _to_async

        dsn_mod = _to_async(settings.database_url)
        if dsn_mod and _db_reachable(str(settings.database_url)):
            _mod_repo = SQLModerationRepo(dsn_mod)  # type: ignore[assignment]
    except Exception:
        pass
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
    register_event_relays(events, notify_topics)
    iam = build_iam_container(settings)
    search = build_search_container()
    # Index incoming events into search
    register_event_indexers(events, search)
    # Tags usage writer (optional; only if DB available)
    try:
        from packages.core.config import to_async_dsn as _to_async

        dsn = _to_async(settings.database_url)
        if dsn:
            register_tags_usage_writer(events, dsn)
    except Exception:
        pass
    media = build_media_container()
    audit = build_audit_container()
    billing = build_billing_container(settings)
    flags = build_flags_container(settings)
    notifications = build_notifications_container(settings)
    users = build_users_container(settings)
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
        achievements_service=achievements_service,
        achievements_admin=achievements_admin,
        worlds_service=worlds_service,
        referrals_service=referrals_service,
        referrals_repo=referrals_repo,
        premium_service=premium_service,
        moderation_service=moderation_service,
        telemetry=telemetry,
        quota=quota,
        iam=iam,
        search=search,
        media=media,
        audit=audit,
        billing=billing,
        flags=flags,
        notifications=notifications,
        users=users,
    )
