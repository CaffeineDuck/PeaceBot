import discord
from discord.ext import commands

from bot.utils.errors import NotPersonalGuild
from bot.utils.mixins.better_cog import BetterCog
from config.personal_guild import personal_guild


class PersonalGuild(BetterCog):
    """
    Extension full of commands only for the
    personal server.
    """

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            return True
        if not ctx.guild.id in personal_guild.ids:
            raise NotPersonalGuild()
        return True

    def cog_help_check(self, ctx: commands.Context):
        if ctx.guild.id in personal_guild.ids:
            return True
        return False

    @commands.command()
    async def gn(self, ctx: commands.Context, user: discord.Member = None):
        """Goodnight Command"""
        user = user or ctx.author
        await ctx.reply(f"Get Naked {user.mention}")

    @commands.command(aliases=["s", "say"])
    async def send(self, ctx, member: discord.Member, *, message="No reason provided"):
        try:
            await member.send(f"{ctx.author.mention} said: {message}")
        except Exception:
            await ctx.reply(f"{member.mention} has his/her DMs closed. :(")

    # TODO: Last to leave VC!
    # @commands.Cog.listener()
    # async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    #     if member.voice


def setup(bot: commands.Bot):
    bot.add_cog(PersonalGuild(bot))
