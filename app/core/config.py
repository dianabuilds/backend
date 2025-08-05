from pydantic import BaseSettings


class Settings(BaseSettings):
    db_username: str
    db_password: str
    db_host: str
    db_port: int
    db_name: str
    db_sslmode: str = "require"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?sslmode={self.db_sslmode}"
        )

    class Config:
        env_file = ".env"


settings = Settings()
