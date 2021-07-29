from typing import Optional

from pydantic import BaseSettings

from .core.helpers.config import DatabaseConfig, LavalinkConfig

__all__ = ("peacebot_config", "peacebot_db_config", "peacebot_lavalink_config")


class PeaceBotConfig(BaseSettings):
    prefix: str
    token: str
    private_bot: Optional[bool]
    load_jishaku: Optional[bool]

    class Config:
        env_file = ".env"
        env_prefix = "bot_"


class PeaceBotDatabaseConfig(BaseSettings, DatabaseConfig):
    class Config:
        env_file = ".env"
        env_prefix = "postgres_"


class PeaceBotLavalinkConfig(BaseSettings, LavalinkConfig):
    class Config:
        env_file = ".env"
        env_prefix = "lavalink_"


peacebot_config = PeaceBotConfig()
peacebot_db_config = PeaceBotDatabaseConfig()
peacebot_lavalink_config = PeaceBotLavalinkConfig()
