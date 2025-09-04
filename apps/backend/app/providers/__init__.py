"""Provider interfaces and registration utilities."""

from punq import Container

from app.core.settings import EnvMode, Settings

from .ai import FakeAIProvider, IAIProvider, RealAIProvider, SandboxAIProvider
from .case_notifier import (
    FakeCaseNotifier,
    ICaseNotifier,
    RealCaseNotifier,
    SandboxCaseNotifier,
)
from .email import FakeEmail, IEmail, RealEmail, SandboxEmail
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
        IEmail: FakeEmail,
        IMediaStorage: FakeMediaStorage,
        ICaseNotifier: FakeCaseNotifier,
    },
    EnvMode.test: {
        IAIProvider: FakeAIProvider,
        IPayments: FakePayments,
        IEmail: FakeEmail,
        IMediaStorage: FakeMediaStorage,
        ICaseNotifier: FakeCaseNotifier,
    },
    EnvMode.staging: {
        IAIProvider: SandboxAIProvider,
        IPayments: SandboxPayments,
        IEmail: SandboxEmail,
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


__all__ = [
    "IAIProvider",
    "IPayments",
    "IEmail",
    "IMediaStorage",
    "ICaseNotifier",
    "register_providers",
]
