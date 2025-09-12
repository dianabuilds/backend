from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Callable, Iterable


def _load_attr(path: str):
    """Load attribute from 'module:attr' spec."""
    if ":" not in path:
        raise ValueError(f"Invalid import path: {path}")
    mod_name, attr = path.split(":", 1)
    mod = importlib.import_module(mod_name)
    return getattr(mod, attr)


@dataclass
class DomainConfig:
    name: str
    routers: list[str] = field(default_factory=list)
    feature_flag: str | None = None  # e.g., 'profile_enabled'
    inits: list[str] = field(default_factory=list)  # callables to run at startup
    providers: list[str] = field(default_factory=list)  # callables (container, settings)
    events: list[str] = field(default_factory=list)  # callables (bus)
    migrations: list[str] = field(default_factory=list)  # optional, reserved for future use
    depends_on: list[str] = field(default_factory=list)

    def is_enabled(self, feature_flags) -> bool:
        if not self.feature_flag:
            return True
        return bool(getattr(feature_flags, self.feature_flag, True))

    def load_routers(self):
        for spec in self.routers:
            yield _load_attr(spec)

    def run_inits(self) -> None:
        for spec in self.inits:
            fn: Callable[[], None] = _load_attr(spec)
            fn()

    def register_providers(self, container, settings) -> None:
        for spec in self.providers:
            fn: Callable[[object, object], None] = _load_attr(spec)
            fn(container, settings)

    def register_event_handlers(self, bus) -> None:
        for spec in self.events:
            fn: Callable[[object], None] = _load_attr(spec)
            fn(bus)


DOMAIN_CONFIGS: list[DomainConfig] = [
    DomainConfig(
        name="auth",
        routers=["app.domains.auth.api.routers:router"],
        providers=[
            "app.domains.auth.infrastructure.container:register_auth_providers",
        ],
    ),
    DomainConfig(
        name="ai",
        routers=["app.domains.ai.api.routers:router"],
    ),
    DomainConfig(
        name="quests",
        routers=["app.domains.quests.api.routers:router"],
    ),
    DomainConfig(
        name="moderation",
        routers=["app.domains.moderation.api.routers:router"],
    ),
    DomainConfig(
        name="notifications",
        routers=[
            "app.domains.notifications.api.routers:router",
            "app.domains.notifications.api.routers:ws_router",
            "app.domains.notifications.api.admin_router:router",
            "app.domains.notifications.api.campaigns_router:router",
        ],
    ),
    DomainConfig(
        name="payments",
        routers=[
            "app.domains.payments.api.routers:router",
            "app.domains.payments.api_admin:router",
        ],
    ),
    DomainConfig(
        name="premium",
        routers=[
            "app.domains.premium.api.routers:router",
            "app.domains.premium.api.admin_router:router",
        ],
    ),
    DomainConfig(
        name="media",
        routers=["app.domains.media.api.routers:router"],
    ),
    DomainConfig(
        name="achievements",
        routers=["app.domains.achievements.api.routers:router"],
    ),
    DomainConfig(
        name="navigation",
        routers=[
            "app.domains.navigation.api.routers:router",
            "app.domains.navigation.api.admin_transitions_router:router",
            "app.domains.navigation.api.admin_transitions_simulate:router",
            "app.domains.navigation.api.admin_echo_router:router",
            "app.domains.navigation.api.admin_traces_router:router",
            "app.domains.navigation.api.admin_navigation_router:router",
        ],
    ),
    DomainConfig(
        name="nodes",
        routers=[
            "app.domains.nodes.api.nodes_router:router",
            "app.domains.nodes.api.my_nodes_router:router",
            "app.domains.nodes.api.articles_admin_router:router",
            "app.domains.nodes.api.admin_nodes_global_router:router",
            "app.domains.nodes.api.admin_nodes_alias_router:router",
            "app.domains.nodes.api.admin_nodes_profiles_router:router",
            "app.domains.nodes.api.admin_drafts_router:router",
        ],
    ),
    DomainConfig(
        name="tags",
        routers=[
            "app.domains.tags.api.public_router:router",
            "app.domains.tags.api.admin_router:router",
        ],
    ),
    DomainConfig(
        name="worlds",
        routers=["app.domains.worlds.api.routers:router"],
    ),
    DomainConfig(
        name="profile",
        routers=["app.domains.profile.api.http:router"],
        feature_flag="profile_enabled",
    ),
    DomainConfig(
        name="search",
        routers=[
            "app.domains.search.api.routers:router",
            "app.domains.search.api.admin_router:router",
        ],
    ),
    DomainConfig(
        name="referrals",
        routers=["app.domains.referrals.api.routers:router"],
    ),
    DomainConfig(
        name="users",
        routers=[
            "app.domains.users.api.routers:router",
            "app.domains.users.api.admin_router:router",
        ],
    ),
    DomainConfig(
        name="admin",
        routers=[
            "app.domains.admin.api.routers:router",
            "app.domains.admin.api.dashboard_router:router",
            "app.domains.admin.api.jobs_router:router",
            "app.domains.admin.api.audit_router:router",
            "app.domains.admin.api.flags_router:router",
            "app.domains.admin.api.cache_router:router",
            "app.domains.admin.api.ratelimit_router:router",
            "app.domains.admin.api.hotfix_patches_router:router",
        ],
        depends_on=["system"],
    ),
]

__all__ = ["DomainConfig", "DOMAIN_CONFIGS"]
