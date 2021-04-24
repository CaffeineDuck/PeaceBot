import re

import discord
from discord import Color, Embed
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
            await ctx.reply(
                f"I am missing the following permissions:\n **{','.join(error.missing_perms)}**"
            )
        elif isinstance(error, commands.MissingPermissions):
            await ctx.reply(
                f"You are missing the following permissions:\n**{','.join(error.missing_perms)}**"
            )
        elif isinstance(error, commands.NSFWChannelRequired):
            image = "https://i.imgur.com/oe4iK5i.gif"
            embed = discord.Embed(
                title="NSFW not allowed here",
                description="Use NSFW commands in a NSFW marked channel.",
                color=discord.Color.dark_blue(),
            )
            embed.set_image(url=image)
            await ctx.reply(embed=embed)
        else:
            title = " ".join(
                re.compile(r"[A-Z][a-z]*").findall(error.__class__.__name__)
            )
            await ctx.reply(
                embed=Embed(title=title, description=str(error), color=Color.red())
            )
            raise error


def setup(bot: commands.Bot):
    bot.add_cog(ErrorHandler(bot))
