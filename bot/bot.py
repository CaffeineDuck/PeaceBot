import re
import traceback
from typing import List

from discord import Color, Embed, Intents, Member, Message
from discord.ext import commands, tasks
from tortoise import Tortoise

from models import GuildModel
from bot.help_command import HelpCommand


class PeaceBot(commands.Bot):
    def __init__(
        self,
        *,
        tortoise_config: dict,
        prefix: str,
        load_extensions: bool = True,
        loadjsk: bool = True
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
            self.load_extensions(("bot.cogs.common", "bot.cogs.config"))
        if loadjsk:
            self.load_extension("jishaku")

    async def determine_prefix(self, bot: commands.Bot, message: Message) -> str:
        guild = message.guild
        if guild:
            guild_model, _ = await GuildModel.get_or_create(id=message.guild.id)
            return commands.when_mentioned_or(guild_model.prefix)(bot, message)
        else:
            return commands.when_mentioned_or(self.prefix)(bot, message)

    @tasks.loop(seconds=0, count=1)
    async def connect_db(self):
        print("Connecting to db")
        await Tortoise.init(self.tortoise_config)
        print("Database connected")

    def load_extensions(self, extentions: List[str]):
        for ext in extentions:
            try:
                self.load_extension(ext)
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)

    async def on_message(self, msg: Message):
        if msg.author.bot:
            return
        await self.process_commands(msg)

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.CommandInvokeError):
            await super().on_command_error(ctx, error)
            await ctx.send("Oopsy, something's broken")
        title = " ".join(re.compile(r"[A-Z][a-z]*").findall(error.__class__.__name__))
        await ctx.send(
            embed=Embed(title=title, description=str(error), color=Color.red())
        )

    async def on_ready(self):
        print("Ready!")
