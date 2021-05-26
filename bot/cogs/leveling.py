import asyncio
from bot.bot import PeaceBot
from bot.utils.leveling_handler import LevelingHandler, UserRank
import random
import re
from typing import List, Optional

import discord
from cachetools import LRUCache
from discord.ext import commands, tasks
from discord.ext.commands import BucketType

from bot.utils.mixins.better_cog import BetterCog
from models import GuildModel, LevelingUserModel


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
        embed.add_field(name="Position", value=f"#{user_rank.position}")
        embed.add_field(name="Level", value=user_rank.level)
        embed.add_field(name="XP", value=f"{user_rank.xp}/{user_rank.required_xp}")

        await ctx.reply(embed=embed)


def setup(bot):
    bot.add_cog(Leveling(bot))