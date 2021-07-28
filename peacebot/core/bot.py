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
        self._config_checker()

    def _config_checker(self, config: BotConfig) -> None:
        """Checks config and handles the bot according to config"""

        if config.db_config:
            asyncio.create_task(self._connect_db(config.db_config)) 

        if config.lavalink_config:
            asyncio.create_task(self._connect_lavalink(config.lavalink_config))
        
        if config.load_jishaku:
            self.load_extension('jishaku')

        self.lock_bot = False


    async def _connect_db(self, db_config: dict) -> None:
        """Connects to the postresql database"""
        pass

    async def _connect_lavalink(self, lavalink_config: LavalinkConfig) -> None:
        """Connects to the lavalink music server"""
        pass
