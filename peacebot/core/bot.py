"""This is the core for `PeaceBot`"""

import asyncio
import logging

import discord
from cachetools import TTLCache
from discord.ext import commands

from peacebot.core.helpers.config import BotConfig, LavalinkConfig

logger = logging.getLogger("peacebot.main")


class PeaceBot(commands.Bot):
    """This is the core `PeaceBot`, the main bot"""

    def __init__(self, config: BotConfig):
        # Passes the args to the commands.Bot's init
        super().__init__(
            command_prefix=config.prefix,
            description=config.description,
        )

        # Config object
        self.config = config

        # Locks the bot from handling on_message events
        self.lock_bot = True

        # Checks and connects to lavalink/DB according to config
        self._config_checker(self.config)

        # Cache Stuffs
        self._guild_model_cache = TTLCache(100, 1000)
        self._user_model_cache = TTLCache(100, 1000)

    def _config_checker(self, config: BotConfig) -> None:
        """Checks config and handles the bot according to config"""

        if config.db_config:
            asyncio.create_task(self._connect_db(config.db_config))

        if config.lavalink_config:
            asyncio.create_task(self._connect_lavalink(config.lavalink_config))

        if config.load_jishaku:
            self.load_extension("jishaku")

    async def _connect_db(self, db_config: dict) -> None:
        """Connects to the postresql database"""
        logger.info("Connected to database")
        self.lock_bot = False

    async def _connect_lavalink(self, lavalink_config: LavalinkConfig) -> None:
        """Connects to the lavalink music server"""
        logger.info("Connected to lavalink server")

    async def _determine_prefix(
        self, bot: commands.Bot, message: discord.Message
    ) -> str:
        """Get the prefix for each command invokation"""

    async def get_local_guild(self, guild_id: int) -> None:
        """Get the Guild Model in the local database"""

    async def get_local_user(self, user_id: int) -> None:
        """Get the User Model in the local database"""

    async def on_message(self, message: discord.Message) -> None:
        """Handles the `messages` for further processing"""
