import os

import discord
from discord.ext import commands
from discord.ext.commands import BucketType

from bot.bot import PeaceBot
from models import GuildModel


class Config(commands.Cog):
    """
    Configure the bot for your guild using the
    commands in this extension.
    """

    def __init__(self, bot: PeaceBot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 10, BucketType.user)
    @commands.bot_has_permissions(send_messages=True, read_messages=True)
    @commands.bot_has_guild_permissions(send_messages=True, read_messages=True)
    @commands.guild_only()
    async def changeprefix(self, ctx: commands.Context, prefix: str):
        if ctx.author is not ctx.guild.owner:
            embed = discord.Embed(
                color=discord.Color.blue(),
                description=f"{ctx.author.mention}, You can't use that.",
            )
            await ctx.send(embed=embed)
        else:
            guild = await GuildModel.from_context(ctx)
            if prefix == guild.prefix:
                embed = discord.Embed(
                    color=discord.Color.blue(),
                    description=f"My prefix for {ctx.guild.name} is already `{prefix}`",
                )
                await ctx.send(embed=embed)
                return
            if guild is not None:
                guild.prefix = prefix
                await guild.save(update_fields=["prefix"])
                self.bot.prefixes_cache[ctx.guild.id] = prefix

            embed = discord.Embed(
                color=discord.Color.blue(),
                description=f"I set your guild's prefix to `{guild.prefix}`",
            )
            await ctx.send(embed=embed)


def setup(bot: PeaceBot):
    bot.add_cog(Config(bot))
