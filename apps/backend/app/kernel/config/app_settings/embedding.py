from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbeddingSettings(BaseSettings):
    """Configuration for vector embeddings."""

    # Preferred provider (e.g. "openai", "cohere", "huggingface", "local", "simple")
    provider: str = "simple"
    # Backward-compatibility: allow EMBEDDING_BACKEND to override provider
    backend: str | None = None
    model: str = ""
    dim: int = 384
    api_base: str = ""
    api_key: str = ""

    model_config = SettingsConfigDict(env_prefix="EMBEDDING_")

    @property
    def name(self) -> str:
        """Return the configured provider/backend name."""
        return (self.provider or self.backend or "simple").lower()

