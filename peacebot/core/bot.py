"""This is the core for `PeaceBot`"""

import asyncio
import logging
from typing import Optional

import discord
import wavelink
from cachetools import TTLCache
from discord.ext import commands
from tortoise import Tortoise

from .helpers.config import BotConfig, LavalinkConfig
from .models import GuildModel

logger = logging.getLogger("peacebot.main")
logging.basicConfig(level=logging.INFO)


class PeaceBot(commands.Bot):
    """This is the core `PeaceBot`, the main bot"""

    def __init__(self, config: BotConfig, tortoise_config: Optional[dict] = None):
        # Passes the args to the commands.Bot's init
        super().__init__(
            command_prefix=config.prefix,
            description=config.description,
        )

        # lock_bot doesn't recieve message until its False
        self.lock_bot = False

        # Config object
        self.config = config
        self.tortoise_config = tortoise_config

        # Checks and connects to lavalink/DB according to config
        self._config_checker(self.config)

        # Cache Stuffs
        self._guild_model_cache = TTLCache(100, 1000)
        self._user_model_cache = TTLCache(100, 1000)

        # Wavelink Client
        self.wavelink_client = wavelink.Client(bot=self)

    @property
    def event_loop(self) -> asyncio.BaseEventLoop:
        """
        This returns the existing event loop
        or creates a event loop and returns it
        """
        return asyncio.get_event_loop()

    def _config_checker(self, config: BotConfig) -> None:
        """Checks config and handles the bot according to config"""

        if config.db_config:
            # Locks the bot from handling on_message events
            self.lock_bot = True
            self.event_loop.create_task(self._connect_db(self.tortoise_config))

        if config.lavalink_config:
            self.event_loop.create_task(self._connect_wavelink(config.lavalink_config))

        if config.load_jishaku:
            self.load_extension("jishaku")

    async def _connect_db(self, tortoise_config: dict) -> None:
        """Connects to the postresql database"""
        if not tortoise_config:
            raise ValueError("Tortoise config must be passed")

        logger.info("Connecting to database")
        await Tortoise.init(tortoise_config)
        logger.info("Connected to database")
        self.lock_bot = False

    async def _connect_wavelink(self, lavalink_config: LavalinkConfig) -> None:
        """Connects to the wavelink nodes"""
        nodes = {
            lavalink_config.identifier: {
                "host": lavalink_config.host,
                "port": lavalink_config.port,
                "password": lavalink_config.password,
                "identifier": lavalink_config.identifier,
                "region": lavalink_config.region,
                "rest_uri": lavalink_config.rest_url,
            }
        }
        [await self.wavelink_client.initiate_node(**node) for node in nodes.values()]
        logger.info("Connected to wavelink nodes")

    async def _determine_prefix(self, _: commands.Bot, message: discord.Message) -> str:
        """Get the prefix for each command invokation"""
        if not message.guild:
            return self.config.prefix

        guild_model = await self.get_local_guild(message.guild.id)
        return guild_model.prefix

    async def get_local_guild(self, guild_id: int) -> GuildModel:
        """Get the Guild Model in the local database"""
        guild_model = self._guild_model_cache.get(guild_id)

        if not guild_model:
            guild_model, _ = await GuildModel.get_or_create(id=guild_id)
            self._guild_model_cache[guild_id] = guild_model

        return guild_model

    async def get_local_user(self, user_id: int) -> None:
        """Get the User Model in the local database"""

    async def on_message(self, message: discord.Message) -> None:
        """Handles the `messages` for further processing"""

        if self.lock_bot:
            return

        if f"<@!{self.user.id}>" == message.content.strip():
            return await message.reply(
                "My prefix here is `{}`".format(
                    await self._determine_prefix(None, message)
                )
            )

        self.process_commands(message)
