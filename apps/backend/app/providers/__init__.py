"""Provider interfaces and registration utilities."""

from punq import Container

from app.kernel.config import EnvMode, Settings

from .ai import FakeAIProvider, IAIProvider, RealAIProvider, SandboxAIProvider
from .case_notifier import (
    FakeCaseNotifier,
    ICaseNotifier,
    RealCaseNotifier,
    SandboxCaseNotifier,
)
from .email import IEmail, RealEmail
from .media_storage import (
    FakeMediaStorage,
    IMediaStorage,
    RealMediaStorage,
    SandboxMediaStorage,
)
from .payments import FakePayments, IPayments, RealPayments, SandboxPayments

EnvMap = dict[type[object], type[object]]

ENV_PROVIDER_MAP: dict[EnvMode, EnvMap] = {
    EnvMode.development: {
        IAIProvider: FakeAIProvider,
        IPayments: FakePayments,
        IEmail: RealEmail,
        IMediaStorage: FakeMediaStorage,
        ICaseNotifier: FakeCaseNotifier,
    },
    EnvMode.test: {
        IAIProvider: FakeAIProvider,
        IPayments: FakePayments,
        IEmail: RealEmail,
        IMediaStorage: FakeMediaStorage,
        ICaseNotifier: FakeCaseNotifier,
    },
    EnvMode.staging: {
        IAIProvider: SandboxAIProvider,
        IPayments: SandboxPayments,
        IEmail: RealEmail,
        IMediaStorage: SandboxMediaStorage,
        ICaseNotifier: SandboxCaseNotifier,
    },
    EnvMode.production: {
        IAIProvider: RealAIProvider,
        IPayments: RealPayments,
        IEmail: RealEmail,
        IMediaStorage: RealMediaStorage,
        ICaseNotifier: RealCaseNotifier,
    },
}


def register_providers(container: Container, settings: Settings) -> None:
    """Register provider implementations in the DI container."""
    mapping = ENV_PROVIDER_MAP.get(settings.env_mode, {})
    for interface, implementation in mapping.items():
        container.register(interface, implementation)

    # Domain-specific providers
    try:  # keep optional to not fail partial deployments
        from app.domains.auth.infrastructure.container import (
            register_auth_providers,
        )

        register_auth_providers(container, settings)
    except Exception:
        # Domains may be optional in some environments; log/ignore here
        pass


__all__ = [
    "IAIProvider",
    "IPayments",
    "IEmail",
    "IMediaStorage",
    "ICaseNotifier",
    "register_providers",
]
