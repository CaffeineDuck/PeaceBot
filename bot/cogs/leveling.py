from bot.bot import PeaceBot
from bot.utils.leveling_handler import LevelingHandler, UserRank
import random
from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import BucketType, Greedy

from bot.utils.mixins.better_cog import BetterCog
from models import LevelingUserModel


class Leveling(BetterCog):
    def __init__(self, bot: PeaceBot):
        super().__init__(bot)
        self._cd = commands.CooldownMapping.from_cooldown(
            1, 60, commands.BucketType.member
        )
        self.leveling_handler = LevelingHandler(self.bot)

    def get_ratelimit(self, message: discord.Message) -> Optional[int]:
        """Returns the ratelimit left"""
        bucket = self._cd.get_bucket(message)
        return bucket.update_rate_limit()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        ratelimit = self.get_ratelimit(message)
        if ratelimit or message.author.bot or not message.guild:
            return
        await self.leveling_handler.handle_user_message(message)

    @commands.Cog.listener()
    async def on_user_level_up(
        self, user_model: LevelingUserModel, message: discord.Message
    ):
        if user_model.level == 1:
            return
            
        guild: discord.Guild = self.bot.get_guild(message.guild.id)
        member = guild.get_member(message.author.id)
        await message.channel.send(
            f"GG {member.mention} has advanced to **Level {user_model.level}**"
        )

    @commands.cooldown(1, 5, BucketType.user)
    @commands.command()
    async def rank(self, ctx: commands.Context, member: Optional[discord.Member]):
        member = member or ctx.author
        user_rank: UserRank = await self.leveling_handler.get_user_rank(member)

        embed = discord.Embed(
            title=f"**{member}**'s Rank",
            description=f"Here is a summary of {member.mention}'s rank!",
            color=discord.Color(random.randint(0, 0xFFFFFF)),
            timestamp=ctx.message.created_at,
        )
        embed.add_field(name="Position", value=f"#{user_rank.position}", inline=False)
        embed.add_field(name="Level", value=user_rank.level, inline=False)
        embed.add_field(
            name="XP", value=f"{user_rank.xp}/{user_rank.required_xp}", inline=False
        )
        embed.add_field(name="Messages Sent", value=user_rank.messages, inline=False)

        await ctx.reply(embed=embed)

    @commands.command(aliases=["ipm6lv"])
    @commands.has_permissions(manage_guild=True)
    async def importmee6levels(self, ctx: commands.Context):
        await ctx.reply(
            "**Please Wait!** The wait time may vary according to the number of members in this server!"
        )
        async with ctx.typing():
            await self.leveling_handler.import_from_mee6(ctx.guild.id)
            await ctx.reply("**Mee6 Data has been imported!**")

    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx: commands.Context):
        guild_model = self.bot.guilds_cache.get(ctx.guild.id)
        user_models = (
            await LevelingUserModel.filter(guild=guild_model)
            .order_by("-xp")
            .prefetch_related("user")
            .limit(10)
        )
        ranks = "\n".join(
            [
                f"**{i+1}.** {ctx.guild.get_member(model.user.id)}"
                for (i, model) in enumerate(user_models)
            ]
        )
        ranks_embed = discord.Embed(
            title="LeaderBoard",
            description=ranks,
            color=discord.Color(random.randint(0, 0xFFFFFF)),
            timestamp=ctx.message.created_at,
        )
        await ctx.reply(embed=ranks_embed)

    @commands.group("lvlcfg", invoke_without_command=True)
    async def leveling_config(self, ctx: commands.Context):
        await ctx.send_help(ctx.command)

    @leveling_config.command(name="enable")
    async def leveling_enable(
        self, ctx: commands.Context, channels: Greedy[discord.TextChannel] = None
    ):
        channels = channels or [ctx.channel]
        await self.leveling_handler.leveling_toggle_handler(channels, ctx, True)

    @leveling_config.command(name="disable")
    async def leveling_disable(
        self, ctx: commands.Context, channels: Greedy[discord.TextChannel] = None
    ):
        channels = channels or [ctx.channel]
        await self.leveling_handler.leveling_toggle_handler(channels, ctx, False)


def setup(bot):
    bot.add_cog(Leveling(bot))
