import re
from typing import List, Tuple

import discord
from cachetools import TTLCache
from discord.ext import commands

from bot.bot import PeaceBot
from bot.utils.mixins.better_cog import BetterCog
from models import AutoResponseModel


class AutoResponseError(commands.CommandError):
    pass


class AutoResponseHandler:
    def __init__(
        self, bot: PeaceBot, message: discord.Message, autoresponse_cache: TTLCache
    ):
        self._bot = bot
        self._message = message
        self._guild_id = message.guild.id
        self._autoresponse_cache = autoresponse_cache

    @property
    def autoresponse_models_cache(self):
        return self._autoresponse_cache

    @autoresponse_models_cache.setter
    def autoresponse_models_cache(self, autoresponse_cache: TTLCache):
        self._autoresponse_cache = autoresponse_cache

    @property
    def discord_message(self):
        return self._message

    @discord_message.setter
    def discord_message(self, new_message: discord.Message):
        self._message = new_message

    async def autoresponses(self):
        return await self.guild_autoresponses(self._guild_id)

    async def filtered_autoresponses(self):
        return await self.guild_filtered_autoresponses(await self.autoresponses())

    async def message_is_valid(self):
        message = self._message
        if (
            message.author.bot
            or message.embeds
            or not message.content
            or not message.guild
        ):
            return False
        return True

    async def guild_autoresponses(self, guild_id: int):
        autoresponses = self._autoresponse_cache.get(guild_id)
        if not autoresponses:
            autoresponses = await self.update_autoresponse_cache(guild_id)
        return autoresponses

    async def guild_filtered_autoresponses(
        self, guild_autoresponses: List[AutoResponseModel]
    ):
        check = lambda m, l: self._message.content.split()[:l] == m.trigger.split()

        try:
            # Gets the first autoresponse object if the sent message is an autoresponse trigger
            filtered_autoresponses = [
                autoresponse
                for autoresponse in guild_autoresponses
                if autoresponse.enabled
                and check(autoresponse, len(autoresponse.trigger.split()))
            ]
            # Sorts the autoresponses according to the length of trigger
            filtered_autoresponses.sort(key=lambda x: x.trigger, reverse=True)
            return filtered_autoresponses[0]
        except IndexError or TypeError as error:
            return

    async def _autoresponse_error_handler(
        self, message: discord.Message, error: Exception
    ):
        title = " ".join(re.compile(r"[A-Z][a-z]*").findall(error.__class__.__name__))
        description = str(error)

        embed = discord.Embed(
            title=title, description=str(error), color=discord.Color.red()
        )
        await self._message.channel.send(embed=embed)
        raise error

    @staticmethod
    async def update_provided_autoresponse_cache(
        guild_id: int, autoresponse_cache: TTLCache
    ):
        autoresponses = await AutoResponseModel.filter(guild__id=guild_id)
        autoresponse_cache[guild_id] = autoresponses
        return (autoresponses, autoresponse_cache)

    async def update_autoresponse_cache(self, guild_id: int) -> List[AutoResponseModel]:
        autoresponses, cache = await self.update_provided_autoresponse_cache(
            guild_id, self._autoresponse_cache
        )
        self._autoresponse_cache = cache
        return autoresponses

    async def _autoresponse_message_formatter(
        self, message: discord.Message, response: str
    ) -> str:
        try:
            # Checks if the mentions is needed in response
            mentioned = message.mentions[0] if "{mentioned" in response else None
        except IndexError:
            raise AutoResponseError("You need to mention someone for this to work!")

        message_content = (
            " ".join(message.content.split(" ")[1:])
            if "{message}" in response
            else None
        )

        if message_content == "":
            raise AutoResponseError(
                "You need to write some extra message for this to work!"
            )

        try:
            updated_message = response.format(
                author=message.author,
                message=message_content,
                raw_message=message,
                server=message.guild,
                mentioned=mentioned,
            )
        except KeyError as error:
            raise AutoResponseError(
                f"""{str(error).replace("'", "`")} is not a valid arguement!"""
            )
        return updated_message

    async def _extra_arguements_handler(self, autoresponse_model: AutoResponseModel):
        len_of_trigger = len(autoresponse_model.trigger.split())

        check = (
            lambda m: self._message.content.split()[:len_of_trigger]
            == m.trigger.split()
        )

        if autoresponse_model.has_variables and check(autoresponse_model):
            output = await self._autoresponse_message_formatter(
                self._message, autoresponse_model.response
            )
        elif autoresponse_model.trigger == self._message.content:
            output = autoresponse_model.response
        elif (
            autoresponse_model.extra_arguements
            and self._message.content.split()[:len_of_trigger]
            == autoresponse_model.trigger.split()
        ):
            output = autoresponse_model.response
        else:
            output = None

        if output:
            return output

    async def run(self):
        try:
            if not await self.message_is_valid():
                return

            filtered_autoresponses = await self.filtered_autoresponses()

            if not filtered_autoresponses:
                return

            output = await self._extra_arguements_handler(filtered_autoresponses)
            return output

        except Exception as error:
            await self._autoresponse_error_handler(self._message, error)
