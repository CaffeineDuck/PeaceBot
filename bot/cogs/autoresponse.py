import re
from typing import Union, List

import discord
from cachetools import TTLCache
from discord import Embed, Color
from discord.ext import commands
from discord.ext.commands import BucketType

from models import AutoResponseModel, GuildModel
from utils.wizard_embed import Prompt, Wizard
from config.personal_guild import personal_guild


class AutoResponseError(commands.CommandError):
    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return self.message


class AutoResponses(commands.Cog):
    """Manage the autoresponses in this server"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.autoresponse_cache = TTLCache(maxsize=1000, ttl=600)

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        autoresponses = self.autoresponse_cache.get(ctx.guild.id)

        if not autoresponses:
            autoresponses = await AutoResponseModel.filter(guild__id=ctx.guild.id)
            self.autoresponse_cache[ctx.guild.id] = autoresponses

        ctx.autoresponses = autoresponses

    async def update_autoresponse_cache(
        self, ctx: commands.Context
    ) -> List[AutoResponseModel]:
        autoresponses = await AutoResponseModel.filter(guild__id=ctx.guild.id)
        self.autoresponse_cache[ctx.guild.id] = autoresponses
        ctx.autoresponses = autoresponses
        return autoresponses

    async def autoresponse_message_formatter(
        self, message: discord.Message, response: str
    ) -> str:
        """Formats the string to a valid message

        Args:
            message (str): Message object to format the string
            response (str): String to format using `message (str)`

        Returns:
            str: Converted string

        Raises:
            KeyError, AttributeError
        """
        try:
            # Checks if the mentions is needed in response
            mention = message.mentions[0] if "{mention}" in response else None
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

        updated_message = response.format(
            author=message.author,
            message=message_content,
            raw_message=message,
            server=message.guild,
            mention=mention,
        )
        return updated_message

    async def autoresponse_error_handler(
        self, message: discord.Message, error: Exception
    ):
        title = " ".join(re.compile(r"[A-Z][a-z]*").findall(error.__class__.__name__))
        description = str(error)

        await message.channel.send(
            embed=Embed(title=title, description=str(error), color=Color.red())
        )

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot or msg.embeds or not msg.content:
            return

        autoresponses = self.autoresponse_cache.get(msg.guild.id)

        if not autoresponses:
            ctx = await self.bot.get_context(msg)
            autoresponses = await self.update_autoresponse_cache(ctx)

        try:
            # Gets the first autoresponse object if the sent message is an autoresponse trigge
            filtered_autoresponse = (
                [
                    autoresponse
                    for autoresponse in autoresponses
                    if autoresponse.trigger == msg.content.split(" ")[0].lower()
                    and autoresponse.enabled
                ]
            )[0]
        except IndexError or TypeError:
            return

        try:
            if filtered_autoresponse.extra_arguements:
                output = await self.autoresponse_message_formatter(
                    msg, filtered_autoresponse.response
                )
            elif filtered_autoresponse.trigger == msg.content:
                output = filtered_autoresponse.response
            else:
                return
            await msg.channel.send(output)

        except Exception as error:
            await self.autoresponse_error_handler(msg, error)

    @commands.group(aliases=["autoresponses"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def autoresponse(self, ctx: commands.Context):
        """Configure Autoresponses"""
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @autoresponse.command(name="toggle", aliases=["change"])
    async def autoresponse_toggle(
        self, ctx: commands.Context, trigger: str, toggle: bool
    ):
        """Enable/ Disable an autoresponse!"""
        record = [
            autoresponse
            for autoresponse in ctx.autoresponses
            if autoresponse.trigger == trigger
        ]

        if not record:
            raise AutoResponseError("This autoresponse doesnot exist in this guild!")

        # Getting the first value from the record as record is a list
        record = record[0]
        record.enabled = toggle
        await record.save(update_fields=["enabled"])

        toggle_str = "enabled" if toggle else "disabled"

        await ctx.send(f"The autoresponse {trigger} has been {toggle_str}")
        await self.update_autoresponse_cache(ctx)

    @autoresponse.command(name="add", aliases=["addresponses", "addautoresponses"])
    async def autoresponse_add(self, ctx: commands.Context):
        """Add new autoresponse"""
        guild = await GuildModel.from_context(ctx)
        prompts = [
            Prompt("Triggered With", description="What shall be the trigger?"),
            Prompt(
                "Reacts With",
                description="What shall be the response?",
            ),
            Prompt(
                "Extra arguements",
                description="Should the autoresponse be triggered even when there is extra message with the trigger?",
                out_type=bool,
                reaction_interface=True,
            ),
        ]

        wizard = Wizard(
            self.bot,
            ctx.author,
            prompts,
            "New Autoresponse",
            completed_message="Autoresponse added successfully!",
            confirm_prompt=True,
        )

        trigger, response, extra_arguements = await wizard.run(ctx.channel)

        record, _ = await AutoResponseModel.get_or_create(
            guild=guild, trigger=trigger.lower()
        )
        record.enabled = True
        record.response = response
        record.extra_arguements = extra_arguements

        await record.save(update_fields=["enabled", "response", "extra_arguements"])
        await self.update_autoresponse_cache(ctx)

    @autoresponse.command(name="delete", aliases=["delresponse", "del"])
    @commands.has_permissions(administrator=True)
    async def autoresponse_delete(self, ctx: commands.Context, trigger: str):
        """Deletes the autoresponse"""
        guild = await GuildModel.from_context(ctx)

        autoresponse = [
            autoresponse
            for autoresponse in ctx.autoresponses
            if autoresponse.trigger == trigger
        ]

        if not autoresponse:
            raise AutoResponseError("This autoresponse doesnot in this guild!")

        prompts = [
            Prompt(
                "Are you sure?",
                description="React to say your message!",
                out_type=bool,
                reaction_interface=True,
            )
        ]

        wizard = Wizard(
            self.bot,
            ctx.author,
            prompts,
            "Delete Autoresponse",
            completed_message="Autoresponse deleted successfully!",
        )
        response = await wizard.run(ctx.channel)

        await AutoResponseModel.get(guild=guild, trigger=trigger).delete()
        await self.update_autoresponse_cache(ctx)

    @autoresponse.command(name="list", aliases=["show", "showall", "all"])
    async def autoresponse_list(self, ctx):
        """Shows the list of all the autoresponses"""

        enabled_autoresponses = [
            f"`{autoresponse.trigger}`"
            for autoresponse in ctx.autoresponses
            if autoresponse.enabled
        ]
        disabled_autoresponses = [
            f"`{autoresponse.trigger}`"
            for autoresponse in ctx.autoresponses
            if not autoresponse.enabled
        ]

        # Creates the list into a string
        enabled_autoresponses = ", ".join(enabled_autoresponses)
        disabled_autoresponses = ", ".join(disabled_autoresponses)

        # Sends the embed with all the enabled autoresponses for that server!
        embed = discord.Embed(title="Autorespones", colour=discord.Color.gold())

        embed.add_field(
            name="Enabled Autoresponses",
            value=enabled_autoresponses
            if enabled_autoresponses
            else "There are no enabled autoresponses in this server!",
            inline=False,
        )
        if disabled_autoresponses:
            embed.add_field(
                name="Disabled Autoresponses",
                value=disabled_autoresponses,
                inline=False,
            )
        embed.set_footer(text=f"Requested by {ctx.author}")

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(AutoResponses(bot))
