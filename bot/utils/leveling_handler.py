import asyncio
from dataclasses import dataclass
import random
import re
from typing import List, Mapping, Tuple

import discord
from cachetools import LRUCache
from discord.ext import commands, tasks

from bot.bot import PeaceBot
from models import GuildModel, LevelingUserModel, UserModel


@dataclass
class UserRank:
    id: int
    xp: int
    position: int
    level: int
    required_xp: int
    guild_model: GuildModel


class UserNotRanked(commands.CommandError):
    def __str__(self):
        return "User Hasn't Been Ranked Yet!"


class LevelingHandler:
    def __init__(self, bot: PeaceBot):
        self._bot = bot
        self._user_cache: Mapping[
            Tuple[discord.Guild.id, discord.Member.id], LevelingUserModel
        ] = LRUCache(1000)

        # This cache is for cross-checking the user models for reducing db queries
        # Using this cache checking takes double the memory but reduces processing
        self._user_check_cache: Mapping[
            Tuple[discord.Guild.id, discord.Member.id], LevelingUserModel
        ] = LRUCache(1000)

        # Starts bulk updating the db from cache
        self.bulk_update_db.start()

    @property
    def cache(self):
        return self._user_cache

    @cache.setter
    def cache(self, cache: LRUCache):
        self._user_cache = cache

    async def get_guild(self, guild_id: int) -> GuildModel:
        guild_model = self._bot.guilds_cache.get(guild_id)

        if not guild_model:
            await asyncio.sleep(2)
            guild_model = await self.get_guild(guild_id)

        return guild_model

    async def get_user(self, user_id: int) -> UserModel:
        user_model = self._bot.users_cache.get(user_id)

        if not user_model:
            await asyncio.sleep(2)
            user_model = await self.get_user(user_id)

        return user_model

    async def get_leveling_user(self, guild_id: int, user_id: int) -> LevelingUserModel:
        leveling_user_model = self._user_cache.get((guild_id, user_id))

        if not leveling_user_model:
            user_model = await self.get_user(user_id)
            guild_model = await self.get_guild(guild_id)

            leveling_user_model, is_new = await LevelingUserModel.get_or_create(
                user=user_model, guild=guild_model
            )
            if is_new:
                await guild_model.xp_members.add(user_model)

        return leveling_user_model

    def required_xp_for_level(self, level: int) -> int:
        return (50 * (level ** 2)) + (100 * level)

    def dispatch_level_up_event(self, user: LevelingUserModel) -> None:
        self._bot.dispatch("user_level_up", user, self._message)

    def update_leveling_cache(self, model: LevelingUserModel) -> None:
        self._user_cache[(model.guild_id, model.user_id)] = model

    async def get_user_level(self, user_model: LevelingUserModel) -> int:
        while True:
            if user_model.xp < self.required_xp_for_level(user_model.level):
                break
            user_model.level += 1
            self.dispatch_level_up_event(user_model)
        return user_model.level
    
    async def get_user_level_from_xp(self, user_model: LevelingUserModel) -> int:
        level = 0
        while True:
            if user_model.xp < self.required_xp_for_level(level):
                break
            level += 1
        return level

    async def update_user_xp_and_level(
        self, user: LevelingUserModel, guild: GuildModel
    ) -> LevelingUserModel:
        user.xp += random.randint(15, 25) * guild.xp_multiplier
        user.level = await self.get_user_level(user)
        return user

    async def handle_user_message(self, message: discord.Message) -> None:
        # Setting the message as it is used all over the class
        self._message = message
        
        guild_model = await self.get_guild(message.guild.id)
        user_model = await self.get_user(message.author.id)
        leveling_user_model = await self.get_leveling_user(guild_model.id, user_model.id)
        updated_user = await self.update_user_xp_and_level(leveling_user_model, guild_model)
        self.update_leveling_cache(updated_user)

    async def get_user_rank(self, member: discord.Member) -> UserRank:
        guild_model = await self.get_guild(member.guild.id)

        leveling_user_models: List[
            LevelingUserModel
        ] = await guild_model.xp_members.all().order_by("xp")
        leveling_user_models.reverse()

        try:
            user_model = list(
                filter(lambda model: model.user_id == member.id, leveling_user_models)
            )[0]
        except IndexError:
            raise UserNotRanked()

        index = leveling_user_models.index(user_model) + 1
        new_level_xp = self.required_xp_for_level(user_model.level)

        user_rank = UserRank(
            member.id, user_model.xp, index, user_model.level, new_level_xp, guild_model
        )
        return user_rank

    @tasks.loop(minutes=1)
    async def bulk_update_db(self) -> None:
        leveling_models = self._user_cache.values()
        bulk_update_tasks = [
            self.save_leveling_models(model) for model in leveling_models
        ]
        await asyncio.gather(*bulk_update_tasks)

    @bulk_update_db.before_loop
    async def before_bulk_db_update(self) -> None:
        await self._bot.wait_until_ready()

    async def save_leveling_models(self, model: LevelingUserModel) -> None:
        check_cache = self._user_check_cache.get((model.guild_id, model.user_id))
        if model == check_cache:
            return
        await model.save()
        self._user_check_cache[(model.guild_id, model.user_id)] = model