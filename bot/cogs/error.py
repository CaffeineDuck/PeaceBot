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
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                f"I am missing the following permissions:\n **{','.join(error.missing_perms)}**"
            )
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(
                f"You are missing the following permissions:\n**{','.join(error.missing_perms)}**"
            )
        else:
            title = " ".join(
                re.compile(r"[A-Z][a-z]*").findall(error.__class__.__name__)
            )
            await ctx.send(
                embed=Embed(title=title, description=str(error), color=Color.red())
            )
            raise error


def setup(bot: commands.Bot):
    bot.add_cog(ErrorHandler(bot))
