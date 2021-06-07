import asyncio
import random
from dataclasses import dataclass
from typing import List, Mapping, Tuple

import aiohttp
import discord
from cachetools import LRUCache
from discord.ext import commands, tasks

from bot.bot import PeaceBot
from models import CommandModel, GuildModel, LevelingUserModel, UserModel


@dataclass
class UserRank:
    id: int
    xp: int
    position: int
    level: int
    required_xp: int
    messages: int
    guild_model: GuildModel


class UserNotRanked(commands.CommandError):
    def __str__(self):
        return "User Hasn't Been Ranked Yet!"


class Mee6DataNotFound(commands.CommandError):
    def __str__(self):
        return "Mee6 data for this guild not found!"


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
            guild_model = self._bot.guilds_cache.get(guild_id)

            if not guild_model:
                guild_model = await GuildModel.get(id=guild_id)

        return guild_model

    async def get_user(self, user_id: int) -> UserModel:
        user_model = self._bot.users_cache.get(user_id)

        if not user_model:
            await asyncio.sleep(2)
            user_model = self._bot.users_cache.get(user_id)

            if not user_model:
                user_model, _ = await UserModel.get_or_create(id=user_id)

        return user_model

    async def get_leveling_user(self, guild_id: int, user_id: int) -> LevelingUserModel:
        leveling_user_model = self._user_cache.get((guild_id, user_id))

        if not leveling_user_model:
            user_model = await self.get_user(user_id)
            guild_model = await self.get_guild(guild_id)

            leveling_user_model, _ = await LevelingUserModel.get_or_create(
                user=user_model, guild=guild_model
            )

        return leveling_user_model

    def required_xp_for_level(self, level: int) -> int:
        return (50 * (level ** 2)) + (100 * level)

    async def level_up_handler(self, user: LevelingUserModel) -> None:
        await user.save()
        await self.role_rewards_handler(user)

        self._bot.dispatch("user_level_up", user)
        self._user_cache[(user.guild_id, user.user_id)] = user

    def update_leveling_cache(self, model: LevelingUserModel) -> None:
        self._user_cache[(model.guild_id, model.user_id)] = model

    async def get_user_level(self, user_model: LevelingUserModel) -> int:
        while True:
            if user_model.xp < self.required_xp_for_level(user_model.level):
                break
            user_model.level += 1
            await self.level_up_handler(user_model)
        return user_model.level

    async def get_user_level_from_xp(self, xp: int) -> int:
        level = 0
        while True:
            if xp < self.required_xp_for_level(level):
                break
            level += 1
        return level

    async def update_user(
        self, user: LevelingUserModel, guild: GuildModel
    ) -> LevelingUserModel:
        user.xp += random.randint(15, 25) * guild.xp_multiplier
        user.messages += 1

        # Updates the user level and triggers level
        # event as well if needed
        user.level = await self.get_user_level(user)

        return user

    async def checks(self, message: discord.Message) -> bool:
        commands_cache = await self._bot.get_commands_cache(message.guild.id)
        check = (
            lambda model: model.name == "leveling-system"
            and not model.enabled
            and (model.channel == "all" or model.channel == message.channel.id)
        )
        valid = [model for model in commands_cache if check(model)]

        if valid:
            return False
        return True

    async def handle_user_message(self, message: discord.Message) -> None:
        if not await self.checks(message):
            return

        # Setting the message as it is used all over the class
        self._message = message

        guild_model = await self.get_guild(message.guild.id)
        user_model = await self.get_user(message.author.id)
        leveling_user_model = await self.get_leveling_user(
            guild_model.id, user_model.id
        )
        # Setting defualt channel so that message can be sent there
        leveling_user_model.defualt_rank_channel = message.channel.id

        updated_user = await self.update_user(leveling_user_model, guild_model)
        self.update_leveling_cache(updated_user)

    async def get_user_rank(self, member: discord.Member) -> UserRank:
        guild_model = await self.get_guild(member.guild.id)

        leveling_user_models: List[LevelingUserModel] = await LevelingUserModel.filter(
            guild=guild_model
        ).order_by("xp")
        leveling_user_models.reverse()

        try:
            user_model = list(
                filter(lambda model: model.user_id == member.id, leveling_user_models)
            )[0]
        except IndexError:
            raise UserNotRanked()

        index = leveling_user_models.index(user_model) + 1

        prev_level_xp = self.required_xp_for_level(user_model.level - 1)
        new_level_xp = self.required_xp_for_level(user_model.level)

        required_xp = new_level_xp - prev_level_xp
        current_xp = user_model.xp - prev_level_xp

        user_rank = UserRank(
            member.id,
            current_xp,
            index,
            user_model.level,
            required_xp,
            user_model.messages,
            guild_model,
        )
        return user_rank

    async def import_from_mee6(self, guild_id: int) -> None:
        async with aiohttp.ClientSession() as cs:
            async with cs.get(
                f"https://mee6.xyz/api/plugins/levels/leaderboard/{guild_id}?limit=999&page=0"
            ) as r:
                if r.status == 404:
                    raise Mee6DataNotFound()
                data = await r.json()

        members = [
            self.update_db_from_other(guild_id, member)
            for member in data.get("players")
        ]
        data = await asyncio.gather(*members)
        await asyncio.create_task(self.mee6_role_rewards_handler(data))

    async def leveling_toggle_handler(
        self, channels: List[discord.TextChannel], ctx: commands.Context, toggle: bool
    ):
        guild_model = self.bot.guilds_cache.get(ctx.guild.id)

        async def save_leveling_togle(channel):
            record, _ = await CommandModel.get_or_create(
                guild=guild_model,
                name="leveling-system",
                channel=channel.id,
            )
            record.enabled = toggle
            await record.save()

        tasks = [save_leveling_togle(channel) for channel in channels]
        asyncio.gather(*tasks)

        channels_str = ", ".join([channel.mention for channel in channels])
        toggle_str = "enabled" if toggle else "disabled"

        await ctx.reply(f"Leveling has been {toggle_str} for channel {channels_str}")

    async def mee6_role_rewards_handler(self, user_models: List[LevelingUserModel]):
        for user in user_models:
            asyncio.create_task(self.role_rewards_handler(user, mee6_import=True))

    async def role_rewards_handler(
        self, user_model: LevelingUserModel, mee6_import: bool = False
    ):
        guild: discord.Guild = self._bot.get_guild(user_model.guild_id)

        try:
            user: discord.Member = await guild.fetch_member(user_model.user_id)
        except discord.HTTPException:
            return

        guild_model = await self._bot.get_guild_model(user_model.guild_id)

        if mee6_import:
            roles = [
                guild.get_role(guild_model.xp_role_rewards.get(str(level)))
                for level in guild_model.xp_role_rewards.keys()
                if int(user_model.level) >= int(level)
            ]
        else:
            roles = [
                guild.get_role(guild_model.xp_role_rewards.get(str(user_model.level)))
            ]

        if not roles:
            return

        print(*roles)
        await user.add_roles(*roles, reason=f"Level up to level {user_model.level}")

    async def update_db_from_other(self, guild_id: int, member: dict) -> None:
        user = await self.get_leveling_user(guild_id, member.get("id"))
        user_level = await self.get_user_level_from_xp(member.get("xp"))

        user.messages = member.get("message_count")
        user.xp = member.get("xp")
        user.level = user_level

        asyncio.create_task(self.save_in_db(user))

        self._user_cache[(user.guild_id, user.user_id)] = user
        self._user_check_cache[(user.guild_id, user.user_id)] = user
        return user

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
        asyncio.create_task(self.save_in_db(model))
        self._user_check_cache[(model.guild_id, model.user_id)] = model

    async def save_in_db(self, model: LevelingUserModel) -> None:
        await model.save()
