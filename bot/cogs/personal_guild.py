import discord
from discord.ext import commands

from config.personal_guild import personal_guild


class NotPersonalGuild(commands.CommandError):
    def __str__(self):
        return "This command can only be used in my personal guild!"


class PersonalGuild(commands.Cog):
    """
    Extension full of commands only for the
    personal server.
    """

    def __init__(self, bot):
        self.bot = bot

    def is_personal_guild(ctx: commands.Context):
        if ctx.guild.id == personal_guild.guild_id:
            return True
        raise NotPersonalGuild()

    @commands.command()
    @commands.check(is_personal_guild)
    async def gn(self, ctx: commands.Context, user: discord.Member = None):
        """Goodnight Command"""
        user = user or ctx.author
        await ctx.send(f"Get Naked {user.mention}")

    @commands.command(aliases=["s", "say"])
    @commands.check(is_personal_guild)
    async def send(self, ctx, member: discord.Member, *, message="No reason provided"):
        try:
            await member.send(f"{ctx.author.mention} said: {message}")
        except Exception:
            await ctx.send(f"{member.mention} has his/her DMs closed. :(")


def setup(bot: commands.Bot):
    bot.add_cog(PersonalGuild(bot))
