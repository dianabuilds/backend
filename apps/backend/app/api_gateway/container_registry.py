from __future__ import annotations

from importlib import import_module
from typing import Any


class ContainerRegistry:
    """Lazy loader for domain containers used by the API gateway."""

    def __init__(self) -> None:
        self._registry: dict[str, str] = {}
        self._cache: dict[str, Any] = {}

    def register(self, key: str, target: str) -> None:
        if ":" not in target:
            raise ValueError(
                f"Invalid target '{target}', expected format 'module:attr'"
            )
        self._registry[key] = target

    def resolve(self, key: str) -> Any:
        if key not in self._registry:
            available = ", ".join(sorted(self._registry))
            raise KeyError(
                f"Container registry key '{key}' is not registered. Known: {available}"
            )
        if key not in self._cache:
            module_path, attr_name = self._registry[key].split(":", 1)
            module = import_module(module_path)
            value = getattr(module, attr_name)
            self._cache[key] = value
        return self._cache[key]


container_registry = ContainerRegistry()

_REGISTRY_ENTRIES = {
    # Platform domains
    "platform.admin.build_container": "domains.platform.admin.wires:build_container",
    "platform.audit.build_container": "domains.platform.audit.wires:build_container",
    "platform.billing.build_container": "domains.platform.billing.wires:build_container",
    "platform.events.RedisEventBus": "domains.platform.events.adapters.event_bus_redis:RedisEventBus",
    "platform.events.RedisOutbox": "domains.platform.events.adapters.outbox_redis:RedisOutbox",
    "platform.events.Events": "domains.platform.events.service:Events",
    "platform.flags.build_container": "domains.platform.flags.wires:build_container",
    "platform.iam.build_container": "domains.platform.iam.wires:build_container",
    "platform.media.build_container": "domains.platform.media.wires:build_container",
    "platform.moderation.build_container": "domains.platform.moderation.wires:build_container",
    "platform.notifications.register_email_channel": "domains.platform.notifications.adapters.email_smtp:register_email_channel",
    "platform.notifications.register_webhook_channel": "domains.platform.notifications.adapters.webhook:register_webhook_channel",
    "platform.notifications.build_container": "domains.platform.notifications.wires:build_container",
    "platform.notifications.register_event_relays": "domains.platform.notifications.wires:register_event_relays",
    "platform.quota.build_container": "domains.platform.quota.wires:build_container",
    "platform.search.build_container": "domains.platform.search.wires:build_container",
    "platform.search.register_event_indexers": "domains.platform.search.wires:register_event_indexers",
    "platform.telemetry.build_container": "domains.platform.telemetry.wires:build_container",
    "platform.users.build_container": "domains.platform.users.wires:build_container",
    # Product domains
    "product.profile.IamClient": "domains.product.profile.adapters.iam_client:IamClient",
    "product.profile.SQLRepo": "domains.product.profile.adapters.repo_sql:create_repo",
    "product.profile.Service": "domains.product.profile.application.services:Service",
    "product.tags.SQLRepo": "domains.product.tags.adapters.repo_sql:create_repo",
    "product.tags.TagUsageStore": "domains.product.tags.adapters.store_memory:TagUsageStore",
    "product.tags.register_usage_writer": "domains.product.tags.adapters.usage_sql_writer:register_tags_usage_writer",
    "product.tags.SQLTagCatalog": "domains.product.tags.adapters.tag_catalog_sql:SQLTagCatalog",
    "product.tags.TagService": "domains.product.tags.application.service:TagService",
    "product.nodes.SQLRepo": "domains.product.nodes.adapters.repo_sql:create_repo",
    "product.nodes.SQLNodeViewsRepo": "domains.product.nodes.adapters.views_sql:create_repo",
    "product.nodes.SQLNodeReactionsRepo": "domains.product.nodes.adapters.reactions_sql:create_repo",
    "product.nodes.SQLNodeCommentsRepo": "domains.product.nodes.adapters.comments_sql:create_repo",
    "product.nodes.RedisNodeViewLimiter": "domains.product.nodes.adapters:RedisNodeViewLimiter",
    "product.nodes.MemoryTagCatalog": "domains.product.nodes.adapters.tag_catalog_memory:MemoryTagCatalog",
    "product.nodes.MemoryUsageProjection": "domains.product.nodes.adapters.usage_memory:MemoryUsageProjection",
    "product.nodes.SQLUsageProjection": "domains.product.nodes.adapters.usage_sql:create_projection",
    "product.nodes.TagUsageStore": "domains.product.tags.adapters.store_memory:TagUsageStore",
    "product.nodes.EmbeddingClient": "domains.product.nodes.application.embedding:EmbeddingClient",
    "product.nodes.register_embedding_worker": "domains.product.nodes.application.embedding_worker:register_embedding_worker",
    "product.nodes.NodeViewsService": "domains.product.nodes.application:NodeViewsService",
    "product.nodes.NodeReactionsService": "domains.product.nodes.application:NodeReactionsService",
    "product.nodes.NodeCommentsService": "domains.product.nodes.application:NodeCommentsService",
    "product.nodes.NodeService": "domains.product.nodes.application.service:NodeService",
    "product.navigation.NodesPort": "domains.product.navigation.application.ports:NodesPort",
    "product.navigation.NavigationService": "domains.product.navigation.application.service:NavigationService",
    "product.ai.LLMRegistry": "domains.product.ai.application.registry:create_registry",
    "product.ai.RegistryProvider": "domains.product.ai.adapters.provider_registry:RegistryBackedProvider",
    "product.ai.FakeProvider": "domains.product.ai.adapters.provider_fake:FakeProvider",
    "product.ai.AIService": "domains.product.ai.application.service:AIService",
    "product.achievements.SQLRepo": "domains.product.achievements.adapters.repo_sql:create_repo",
    "product.achievements.Service": "domains.product.achievements.application.service:AchievementsService",
    "product.achievements.AdminService": "domains.product.achievements.application.service:AchievementsAdminService",
    "product.worlds.SQLRepo": "domains.product.worlds.adapters.repo_sql:create_repo",
    "product.worlds.Service": "domains.product.worlds.application.service:WorldsService",
    "product.referrals.SQLRepo": "domains.product.referrals.adapters.repo_sql:create_repo",
    "product.referrals.Service": "domains.product.referrals.application.service:ReferralsService",
    "product.premium.Service": "domains.product.premium.application.service:PremiumService",
    "product.quests.SQLRepo": "domains.product.quests.adapters.repo_sql:create_repo",
    "product.quests.Service": "domains.product.quests.application.service:QuestService",
    "product.moderation.SQLRepo": "domains.product.moderation.adapters.repo_sql:create_repo",
    "product.moderation.Service": "domains.product.moderation.application.service:ModerationService",
}

for key, target in _REGISTRY_ENTRIES.items():
    container_registry.register(key, target)
