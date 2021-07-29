"""This modules parses environment variables"""

# pylint: disable=R0903

from typing import Optional

from pydantic import BaseSettings

from .core.helpers.config import DatabaseConfig, LavalinkConfig

__all__ = ("peacebot_config", "peacebot_db_config", "peacebot_lavalink_config")


class PeaceBotConfig(BaseSettings):
    """
    Parses PeaceBot config with environment variables
    """

    prefix: str
    token: str
    private_bot: Optional[bool]
    load_jishaku: Optional[bool]

    class Config:
        """This is the config class containg info about env prefix and file"""

        env_file = ".env"
        env_prefix = "bot_"


class PeaceBotDatabaseConfig(BaseSettings, DatabaseConfig):
    """
    Parses PeaceBot Database config with environment variables
    """

    class Config:
        """This is the config class containg info about env prefix and file"""

        env_file = ".env"
        env_prefix = "postgres_"


class PeaceBotLavalinkConfig(BaseSettings, LavalinkConfig):
    """
    Parses PeaceBot Database config with environment variables
    """

    class Config:
        """This is the config class containg info about env prefix and file"""

        env_file = ".env"
        env_prefix = "lavalink_"


peacebot_config = PeaceBotConfig()
peacebot_db_config = PeaceBotDatabaseConfig()
peacebot_lavalink_config = PeaceBotLavalinkConfig()
