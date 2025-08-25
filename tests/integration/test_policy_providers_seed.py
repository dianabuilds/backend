import pytest
from punq import Container

from apps.backend.app.core.policy import RuntimePolicy
from apps.backend.app.core.rng import init_rng, next_seed
from apps.backend.app.core.settings import Settings, EnvMode
from apps.backend.app.providers import (
    register_providers,
    IAIProvider,
    IPayments,
    IEmail,
    IMediaStorage,
)
from apps.backend.app.providers.ai import FakeAIProvider
from apps.backend.app.providers.email import FakeEmail
from apps.backend.app.providers.media_storage import FakeMediaStorage
from apps.backend.app.providers.payments import FakePayments


@pytest.mark.asyncio
async def test_runtime_policy_in_testing_env(monkeypatch):
    monkeypatch.setenv("TESTING", "True")
    monkeypatch.delenv("RATE_LIMIT_MODE", raising=False)
    policy = RuntimePolicy.from_env()
    assert policy.allow_write is False
    assert policy.rate_limit_mode == "disabled"


def test_register_providers_uses_fakes():
    container = Container()
    settings = Settings(env_mode=EnvMode.test)
    register_providers(container, settings)

    assert isinstance(container.resolve(IAIProvider), FakeAIProvider)
    assert isinstance(container.resolve(IPayments), FakePayments)
    assert isinstance(container.resolve(IEmail), FakeEmail)
    assert isinstance(container.resolve(IMediaStorage), FakeMediaStorage)


def test_init_rng_fixed_seed(monkeypatch):
    monkeypatch.setenv("RNG_SEED", "123")
    init_rng("fixed")
    first = next_seed()

    monkeypatch.setenv("RNG_SEED", "123")
    init_rng("fixed")
    second = next_seed()

    assert first == second
