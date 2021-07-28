from peacebot.core.config import BotConfig, LavalinkConfig
import discord
from discord.ext import commands
import asyncio


class PeaceBot(commands.Bot):
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
        self.config_checker()

    def config_checker(self, config: BotConfig) -> None:
        """Connects to respective services according to the config"""

        if config.db_config:
            asyncio.create_task(self.connect_db(config.db_config)) 
        if config.lavalink_config:
            asyncio.create_task(self.connect_lavalink(config.lavalink_config))

        self.lock_bot = False


    async def connect_db(self, db_config: dict) -> None:
        """Connects to the postresql database"""
        pass

    async def connect_lavalink(self, lavalink_config: LavalinkConfig) -> None:
        """Connects to the lavalink music server"""
        pass
