from apps.backend.app.api_gateway.container_registry import container_registry

# Keys covering domains migrated to adapters.sql/memory layout.
_RESOLUTION_KEYS = [
    "product.profile.SQLRepo",
    "product.tags.SQLRepo",
    "product.tags.SQLTagCatalog",
    "product.tags.register_usage_writer",
    "product.nodes.SQLRepo",
    "product.nodes.SQLUsageProjection",
    "product.achievements.SQLRepo",
    "product.worlds.SQLRepo",
    "product.referrals.SQLRepo",
    "product.quests.SQLRepo",
    "product.moderation.SQLRepo",
    "platform.audit.build_container",
    "platform.billing.build_container",
    "platform.iam.build_container",
    "platform.notifications.build_container",
]


def test_container_registry_resolves_migrated_keys():
    for key in _RESOLUTION_KEYS:
        value = container_registry.resolve(key)
        assert value is not None, f"container registry returned nothing for {key}"
