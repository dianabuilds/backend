from pydantic_settings import BaseSettings, SettingsConfigDict

class NavigationSettings(BaseSettings):
    max_options: int = 3
    weight_compass: float = 0.5
    weight_echo: float = 0.3
    weight_random: float = 0.2
    no_repeat_last_n: int = 3

    model_config = SettingsConfigDict(env_prefix="NAV_")
