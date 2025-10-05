from packages.core.config import Settings
from domains.product.ai.application.registry import create_registry


def test_create_registry_in_test_env_uses_memory_backend():
    settings = Settings(env="test")
    registry = create_registry(settings)
    assert registry._backend.__class__.__name__ == "_MemoryBackend"


def test_create_registry_with_explicit_dsn_uses_sql_backend():
    settings = Settings()
    registry = create_registry(
        settings,
        dsn="postgresql+asyncpg://app:app@localhost:5432/app",
    )
    assert registry._backend.__class__.__name__ == "_SQLBackend"
