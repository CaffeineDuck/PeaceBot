from typing import Optional

import discord
from discord.ext import commands


class Utils(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="avatar", aliases=["av"])
    async def show_avatar(
        self, ctx: commands.Context, member: Optional[discord.Member]
    ):
        member = member or ctx.author

        embed = discord.Embed(title="Avatar", colour=discord.Color.blue())
        embed.set_author(name=member, url=member.avatar_url, icon_url=member.avatar_url)
        embed.set_image(url=member.avatar_url)
        embed.set_footer(text=f"Requested by {ctx.author}")

        await ctx.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Utils(bot))
