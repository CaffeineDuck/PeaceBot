import asyncio
import random
from typing import List, Optional
from cachetools import LRUCache

import discord
from discord.ext import commands, tasks
from discord.ext.commands import BucketType

from bot.utils.mixins.better_cog import BetterCog
from models import GuildModel, LevelingUserModel


class Leveling(BetterCog):
    def __init__(self, bot):
        super().__init__(bot)
        self._cd = commands.CooldownMapping.from_cooldown(
            1, 60, commands.BucketType.member
        )
        self.bulk_update_db.start()
        self.users_leveling_cache = LRUCache(1000)

        # This cache is for cross-checking the user models for reducing db queries
        self.users_leveling_cache_updated = LRUCache(1000)

    def get_ratelimit(self, message: discord.Message) -> Optional[int]:
        """Returns the ratelimit left"""
        bucket = self._cd.get_bucket(message)
        return bucket.update_rate_limit()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        ratelimit = self.get_ratelimit(message)
        if ratelimit or message.author.bot or not message.guild:
            return

        leveling_user = self.users_leveling_cache.get(
            (message.guild.id, message.author.id)
        )

        guild_model = self.bot.guilds_cache.get(message.guild.id)

        if not guild_model:
            # Sleeping for 2 sec so that cache can be created if not there!
            await asyncio.sleep(2)
            guild_model = self.bot.guilds_cache.get(message.guild.id)

        if not leveling_user:
            leveling_user, is_new = await LevelingUserModel.get_or_create(user__id = message.author.id, guild__id = message.guild.id)
            if is_new:
                await guild_model.xp_members.add(leveling_user)

        user_leveling_model = await self.give_user_xp(leveling_user, guild_model)

        self.users_leveling_cache[
            (message.guild.id, message.author.id)
        ] = user_leveling_model

    async def give_user_xp(self, user: LevelingUserModel, guild: GuildModel):
        user.xp += random.randint(15, 25) * guild.xp_multiplier
        user.level = await self.get_level(user)
        return user

    async def get_level(self, user: LevelingUserModel):
        while True:
            if user.xp < ((50 * (user.level ** 2)) + (50 * user.level)):
                break
            user.level += 1
        return user.level

    @tasks.loop(minutes=1)
    async def bulk_update_db(self):
        leveling_models = self.users_leveling_cache.values()
        bulk_update_tasks = [
            self.save_leveling_model(model) for model in leveling_models
        ]
        await asyncio.gather(*bulk_update_tasks)

    async def save_leveling_model(self, model: LevelingUserModel):
        model_cache = self.users_leveling_cache_updated.get(
            (model.guild_id, model.user_id)
        )
        if model == model_cache:
            return

        await model.save()
        self.users_leveling_cache_updated[(model.guild_id, model.user_id)] = model

    @bulk_update_db.before_loop
    async def before_bulk_db_update(self):
        await self.bot.wait_until_ready()

    @commands.cooldown(1,5, BucketType.user)
    @commands.command()
    async def rank(self, ctx: commands.Context, member: Optional[discord.Member]):
        member = member or ctx.author
        guild_model: GuildModel = self.bot.guilds_cache.get(ctx.guild.id)

        leveling_user_models: List[LevelingUserModel] = await guild_model.xp_members.all().order_by('xp')
        leveling_user_models.reverse()

        user_model = list(filter(lambda model: model.user_id == member.id, leveling_user_models))[0]
        index = (leveling_user_models.index(user_model) + 1)

        embed = discord.Embed(
            title=f"**{member}**'s Rank",
            description=f"Here is a summary of {member.mention}'s rank!",
            color=discord.Color(random.randint(0, 0xFFFFFF)),
            timestamp=ctx.message.created_at,
        )
        embed.add_field(name='Position', value=f'#{index}')
        embed.add_field(name='Level', value=user_model.level)
        embed.add_field(name='XP', value=user_model.xp)

        await ctx.reply(embed=embed)



def setup(bot):
    bot.add_cog(Leveling(bot))
