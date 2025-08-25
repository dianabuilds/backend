from pydantic_settings import BaseSettings, SettingsConfigDict

class CompassSettings(BaseSettings):
    top_k_db: int = 200
    top_k_result: int = 20
    pgv_probes: int = 10

    model_config = SettingsConfigDict(env_prefix="COMPASS_")
