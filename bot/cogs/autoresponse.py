import re
from typing import List, Union

import discord
from cachetools import TTLCache
from discord import Color, Embed
from discord.ext import commands
from discord.ext.commands import BucketType

from bot.bot import PeaceBot
from bot.utils.autoresponse_handler import AutoResponseError, AutoResponseHandler
from bot.utils.wizard_embed import Prompt, Wizard
from config.personal_guild import personal_guild
from models import AutoResponseModel, GuildModel


class AutoResponses(commands.Cog):
    """Manage the autoresponses in this server"""

    def __init__(self, bot: PeaceBot):
        self.bot = bot
        self.autoresponse_cache = TTLCache(maxsize=1000, ttl=600)

    # Runs before every command invokation
    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        autoresponses = self.autoresponse_cache.get(ctx.guild.id)

        if not autoresponses:
            autoresponses = await AutoResponseModel.filter(guild__id=ctx.guild.id)
            self.autoresponse_cache[ctx.guild.id] = autoresponses

        ctx.autoresponses = autoresponses

    # Runs after every command invokation
    async def cog_after_invoke(self, ctx: commands.Context) -> None:
        if ctx.command == self.autoresponse_list:
            return
        cache = (
            await AutoResponseHandler.update_provided_autoresponse_cache(
                ctx.guild.id, self.autoresponse_cache
            )
        )[1]
        self.autoresponse_cache = cache

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        autoresponse_handler = AutoResponseHandler(
            self.bot, msg, self.autoresponse_cache
        )

        output = await autoresponse_handler.run()
        self.autoresponse_cache = autoresponse_handler.autoresponse_models_cache

        if not output:
            return

        await msg.channel.send(output)

    @commands.group(aliases=["autoresponses"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def autoresponse(self, ctx: commands.Context):
        """Configure Autoresponses"""
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @commands.cooldown(1, 10, BucketType.user)
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

    @commands.cooldown(1, 60, BucketType.user)
    @autoresponse.command(name="add", aliases=["addresponses", "addautoresponses"])
    async def autoresponse_add(self, ctx: commands.Context):
        """
        Add new autoresponse

        **Allowed Variables:**
        Message Author: `author`
        Message Content: `message`
        Server: `server`
        Mentioned Person: `mentioned`

        *Note: Use `{` `}`for variables. Eg: `Hi {author.mention}`*
        """
        guild = await GuildModel.from_context(ctx)
        prompts = [
            Prompt("Triggered With", description="What shall be the trigger?"),
            Prompt(
                "Reacts With",
                description="What shall be the response?",
            ),
            Prompt(
                "Extra Arguements",
                description="Should the autoresponse be triggered even when there is extra message with the trigger?",
                out_type=bool,
                reaction_interface=True,
            ),
            Prompt(
                "Has Variables",
                description="Does the response of the autoresponse have any variables?",
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

        trigger, response, extra_arguements, has_variables = await wizard.run(
            ctx.channel
        )

        record, _ = await AutoResponseModel.get_or_create(
            guild=guild, trigger=trigger.lower()
        )
        record.enabled = True
        record.response = response
        record.extra_arguements = extra_arguements
        record.has_variables = has_variables

        await record.save(
            update_fields=["enabled", "response", "extra_arguements", "has_variables"]
        )

    @autoresponse.command(name="delete_all", aliases=["dall", "remall"])
    @commands.cooldown(1, 500, BucketType.user)
    @commands.has_permissions(administrator=True)
    async def autoresponse_delete_all(self, ctx: commands.Context):
        """Delete all the autoresponses in the guild"""
        guild = await GuildModel.from_context(ctx)
        await AutoResponseModel.filter(guild=guild).delete()
        await ctx.send("All autoresponses for this guild have been deleted!")

    @autoresponse.command(name="delete", aliases=["delresponse", "del"])
    @commands.cooldown(1, 10, BucketType.user)
    async def autoresponse_delete(self, ctx: commands.Context, trigger: str):
        """Deletes the autoresponse"""
        guild = await GuildModel.from_context(ctx)

        autoresponse = [
            autoresponse
            for autoresponse in ctx.autoresponses
            if autoresponse.trigger == trigger
        ]

        if not autoresponse:
            raise AutoResponseError("This autoresponse doesnot exist in this guild!")

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


def setup(bot: PeaceBot):
    bot.add_cog(AutoResponses(bot))
