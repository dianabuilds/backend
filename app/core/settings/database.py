from pydantic_settings import BaseSettings, SettingsConfigDict

class DatabaseSettings(BaseSettings):
    username: str = ""
    password: str = ""
    host: str = ""
    port: int = 5432
    name: str = ""
    sslmode: str = "require"

    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800
    echo: bool = False

    model_config = SettingsConfigDict(extra="ignore")

    @property
    def url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )

    @property
    def connect_args(self) -> dict:
        args: dict = {}
        if self.sslmode == "require":
            args["ssl"] = True
        return args
