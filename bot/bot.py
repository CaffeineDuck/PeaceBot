import logging
import os
import traceback
from itertools import cycle
from typing import List

import discord
import watchgod
from aiohttp import ClientSession
from cachetools import LRUCache
from discord import Intents, Message
from discord.ext import commands, tasks
from tortoise import Tortoise

from bot.help_command import HelpCommand
from bot.utils.errors import CommandDisabled
from models import CommandModel, GuildModel, UserModel

logging.basicConfig(level=logging.INFO)


class PeaceBot(commands.Bot):
    def __init__(
        self,
        *,
        tortoise_config: dict,
        prefix: str,
        log_webhook_url: str,
        load_extensions: bool = True,
        loadjsk: bool = True,
        developement_environment: bool = True,
    ):
        super().__init__(
            command_prefix=self.determine_prefix,
            intents=Intents.all(),
            help_command=HelpCommand(),
            case_insensitive=True,
        )
        self.tortoise_config = tortoise_config
        self.developement_environment = developement_environment
        self.log_webhook_url = log_webhook_url
        self.connect_db.start()
        self.prefix = prefix
        self.prefixes_cache = LRUCache(1000)
        self.commands_cache = LRUCache(1000)
        self.users_cache = LRUCache(1000)
        self.guilds_cache = LRUCache(1000)
        self.add_check(self.check)

        # Makes the cog-help case insensivite
        self._botBase__cogs = commands.core._CaseInsensitiveDict()

        if load_extensions:
            self.load_extensions(
                (
                    "bot.cogs.core",
                    "bot.cogs.config",
                    "bot.cogs.personal_guild",
                    "bot.cogs.snipe",
                    "bot.cogs.emoji",
                    "bot.cogs.moderation",
                    "bot.cogs.nsfw",
                    "bot.cogs.autoresponse",
                    "bot.cogs.fun",
                    "bot.cogs.misc",
                    "bot.cogs.utils",
                    "bot.cogs.reddit",
                    "bot.cogs.animals",
                    "bot.cogs.code_exec",
                    "bot.cogs.error",
                    "bot.cogs.prabhidhikaar",
                    "bot.cogs.leveling",
                    "bot.cogs.image",
                    "bot.cogs.music",
                )
            )

        if loadjsk:
            self.load_extension("jishaku")

        # Started the status chaning cycle
        self._statuses = cycle(
            [
                lambda: discord.Activity(
                    type=discord.ActivityType.watching,
                    name=f"{self.prefix}help | Use {self.prefix}invite to invite me 👀",
                ),
                lambda: discord.Activity(
                    type=discord.ActivityType.listening,
                    name=f"{len(self.commands)} Commands | {len(self.users)} Users | {len(self.guilds)} Servers",
                ),
                lambda: discord.Activity(
                    type=discord.ActivityType.watching,
                    name=f"My updates | Use {self.prefix}source to see the source 😏",
                ),
            ]
        )
        self.change_status.start()

    # Determine the unique prefix for each guild
    async def cache_guild_prefix(self, message: Message) -> None:
        guild_model = await GuildModel.from_guild_object(message.guild)
        self.prefixes_cache[message.guild.id] = guild_model.prefix
        return guild_model.prefix

    async def determine_prefix(self, bot: commands.Bot, message: Message) -> str:
        guild = message.guild
        if not guild:
            return commands.when_mentioned_or(self.prefix)(bot, message)

        prefix = self.prefixes_cache.get(guild.id)
        if not prefix:
            prefix = await self.cache_guild_prefix(message)

        return commands.when_mentioned_or(prefix)(bot, message)

    # Properties
    @property
    def session(self) -> ClientSession:
        return self.http._HTTPClient__session

    @property
    def log_webhook(self) -> discord.Webhook:
        return discord.Webhook.from_url(
            self.log_webhook_url, adapter=discord.AsyncWebhookAdapter(self.session)
        )

    # Loops for connecting db, watching cogs and changing status
    @tasks.loop(seconds=0, count=1)
    async def connect_db(self):
        logging.info("Connecting to db")
        await Tortoise.init(self.tortoise_config)
        logging.info("Database connected")

    @tasks.loop(seconds=10)
    async def change_status(self):
        new_activity = next(self._statuses)
        await self.change_presence(status=discord.Status.idle, activity=new_activity())

    @change_status.before_loop
    async def before_change_status(self):
        await self.wait_until_ready()

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
                            logging.info(f"AutoReloaded {extension_name}.")
                    else:
                        try:
                            self.unload_extension(extension_name)
                            logging.info(f"AutoUnloaded {extension_name}.")
                        except commands.ExtensionNotLoaded:
                            pass
                except (commands.ExtensionFailed, commands.NoEntryPointError) as e:
                    traceback.print_exception(type(e), e, e.__traceback__)

    # Function to load extension
    def load_extensions(self, extentions: List[str]):
        for ext in extentions:
            try:
                self.load_extension(ext)
                logging.info(f"Loaded {ext}")
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)

    # On Message checks
    async def on_message(self, message: Message):
        if message.guild == None:
            await self.process_commands(message)

        user = self.users_cache.get(message.author.id)
        guild = self.guilds_cache.get(message.guild.id)

        if not guild:
            guild, _ = await GuildModel.get_or_create(id=message.guild.id)
            self.guilds_cache[message.guild.id] = guild

        if not user:
            user, is_new = await UserModel.get_or_create(id=message.author.id)
            self.users_cache[message.author.id] = user

            if is_new:
                await guild.users.add(user)

        await self.process_commands(message)

    # Creates a guild model on joining guild
    async def on_guild_join(self, guild: discord.Guild):
        await GuildModel.get_or_create(id=guild.id)

    # DB models caching handlers
    async def get_commands_cache(self, guild_id: int) -> List[CommandModel]:
        commands_cache = self.commands_cache.get(guild_id)

        if not commands_cache:
            commands_cache = await CommandModel.filter(guild__id=guild_id)
            self.commands_cache[guild_id] = commands_cache

        return commands_cache

    async def get_guild_model(self, guild_id: int):
        guild_model = self.guilds_cache.get(guild_id)

        if not guild_model:
            guild_model, _ = await GuildModel.get_or_create(id=guild_id)

        return guild_model

    async def get_user_model(self, user_id: int):
        user_model = self.users_cache.get(user_id)

        if not user_model:
            user_model = await UserModel.get(id=user_id)
            self.users_cache[user_id] = user_model

        return user_model

    # Custom channel check for running commands
    # TODO: Add permission/ role check!
    async def check(self, ctx: commands.Context):
        if not ctx.guild:
            return True

        commands_cache = await self.get_commands_cache(ctx.guild.id)

        defualt_check = (
            lambda ctx, command: not command.enabled
            and ctx.channel.id == command.channel
        )
        command_check = (
            lambda ctx, command: not command.is_cog
            and ctx.command.name.lower() == command.name.lower()
        )
        cog_check = (
            lambda ctx, cog: cog.is_cog
            and ctx.cog
            and cog.name.lower() == ctx.cog.qualified_name.lower()
        )

        current_command = [
            command.name
            for command in commands_cache
            if defualt_check(ctx, command)
            and (command_check(ctx, command) or cog_check(ctx, command))
        ]
        if current_command:
            raise CommandDisabled(ctx.command.name, ctx.cog.qualified_name)
        return True

    # Gets or create member model from db
    async def get_or_fetch_member(
        self, guild: discord.Guild, member_id: int
    ) -> discord.Member:

        member = guild.get_member(member_id)
        if member is not None:
            return member

        shard = self.get_shard(guild.shard_id)
        if shard.is_ws_ratelimited():
            try:
                member = await guild.fetch_member(member_id)
            except discord.HTTPException:
                return None
            else:
                return member

        members = await guild.query_members(limit=1, user_ids=[member_id], cache=True)
        if not members:
            return None
        return members[0]

    # On ready methods
    async def on_ready(self):
        logging.info(f"Logged in as {self.user.name}#{self.user.discriminator}")
        if self.developement_environment:
            self.cog_watcher_task.start()
        logging.info("Ready")
