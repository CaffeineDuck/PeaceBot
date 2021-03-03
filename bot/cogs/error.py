import re

import discord
from discord import Embed, Color
from discord.ext import commands


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send("Oopsy, something's broken")
            title = " ".join(
                re.compile(r"[A-Z][a-z]*").findall(error.__class__.__name__)
            )
            await ctx.send(
                embed=Embed(title=title, description=str(error), color=Color.red())
            )


def setup(bot: commands.Bot):
    bot.add_cog(ErrorHandler(bot))
