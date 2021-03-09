import os
import re
import logging
import traceback
from typing import List

import watchgod
from discord import Color, Embed, Intents, Member, Message
from discord.ext import commands, tasks
from tortoise import Tortoise

from models import GuildModel
from bot.help_command import HelpCommand

logging.basicConfig(level=logging.INFO)


class PeaceBot(commands.Bot):
    def __init__(
        self,
        *,
        tortoise_config: dict,
        prefix: str,
        load_extensions: bool = True,
        loadjsk: bool = True,
    ):
        super().__init__(
            command_prefix=self.determine_prefix,
            intents=Intents.all(),
            help_command=HelpCommand(),
        )
        self.tortoise_config = tortoise_config
        self.connect_db.start()
        self.prefix = prefix

        if load_extensions:
            self.load_extensions(
                (
                    "bot.cogs.core",
                    "bot.cogs.config",
                    "bot.cogs.personal_guild",
                    "bot.cogs.error",
                    "bot.cogs.snipe",
                    "bot.cogs.emoji",
                    "bot.cogs.moderation",
                    "bot.cogs.nsfw",
                    "bot.cogs.autoresponse",
                    "bot.cogs.fun",
                    "bot.cogs.misc",
                )
            )
        if loadjsk:
            self.load_extension("jishaku")

    async def determine_prefix(self, bot: commands.Bot, message: Message) -> str:
        guild = message.guild
        if guild:
            guild_model = await GuildModel.from_guild_object(message.guild)
            return commands.when_mentioned_or(guild_model.prefix)(bot, message)
        else:
            return commands.when_mentioned_or(self.prefix)(bot, message)

    @tasks.loop(seconds=0, count=1)
    async def connect_db(self):
        print("Connecting to db")
        await Tortoise.init(self.tortoise_config)
        print("Database connected")

    @tasks.loop(seconds=1)
    async def cog_watcher_task(self) -> None:
        """Watches the cogs directory for changes and reloads files"""
        async for change in watchgod.awatch(
            "bot/cogs", watcher_cls=watchgod.PythonWatcher
        ):
            for change_type, changed_file_path in change:
                try:
                    extension_name = changed_file_path.replace(os.path.sep, ".")[:-3]
                    if len(extension_name) > 36 and extension_name[-33] == ".":
                        continue
                    if change_type == watchgod.Change.modified:
                        try:
                            self.unload_extension(extension_name)
                        except commands.ExtensionNotLoaded:
                            pass
                        finally:
                            self.load_extension(extension_name)
                            print(f"AutoReloaded {extension_name}.")
                    else:
                        try:
                            self.unload_extension(extension_name)
                            print(f"AutoUnloaded {extension_name}.")
                        except commands.ExtensionNotLoaded:
                            pass
                except (commands.ExtensionFailed, commands.NoEntryPointError) as e:
                    traceback.print_exception(type(e), e, e.__traceback__)

    def load_extensions(self, extentions: List[str]):
        for ext in extentions:
            try:
                self.load_extension(ext)
                print(f"Loaded {ext}")
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)

    async def on_ready(self):
        print(f"Logged in as {self.user.name}#{self.user.discriminator}")
        self.cog_watcher_task.start()
        print("Ready")
