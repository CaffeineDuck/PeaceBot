from typing import Union

import discord
from discord.ext import commands
from discord.ext.commands import BucketType

from models import AutoResponseModel, GuildModel
from utils.wizard_embed import Wizard, Prompt
from config.personal_guild import personal_guild


class AutoResponseDoesNotExist(commands.CommandError):
    def __str__(self):
        return "This autoresponse doesnot in this guild!"


class AutoResponses(commands.Cog):
    """Manage the autoresponses in this server"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def commands_checker(self, command: str, guild_id: int) -> bool:
        """Checks if the autoresponse is enabled and exists in that server!

        Args:
                        command (str): Command for the autoresponse
                        guild_id (int): Id of the guild

        Returns:
                        bool: Autoresponse exists and is enabled in that guild
        """
        return await AutoResponseModel.exists(
            guild__id=guild_id, trigger=command, enabled=True
        )

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
        message_content = " ".join(message.content.split(" ")[1:])
        updated_message = response.format(
            author=message.author,
            message=message_content,
            raw_message=message,
            server=message.guild,
        )
        return updated_message

    # On message listner to give the autoresponse if it matches the trigger!
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        # Loops through all the custom autoresponses (GUILD SPECIFIC)
        autoresponses = await AutoResponseModel.filter(
            guild__id=msg.guild.id, enabled=True
        )
        for data in autoresponses:
            if msg.content.split(" ")[0].lower() == data.trigger:
                await msg.channel.send(
                    await self.autoresponse_message_formatter(msg, data.response)
                )
                return

    @commands.group(aliases=["autoresponses"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def autoresponse(self, ctx: commands.Context):
        """Configure Autoresponses"""
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @autoresponse.command(name="toggle", aliases=["change"])
    async def autoresponse_toggle(
        self, ctx: commands.Context, trigger: str, is_enabled: bool
    ):
        """Enable/ Disable an autoresponse!"""
        # Checks if the trigger and response exists in that guild and works accordingly!
        record = await AutoResponseModel.get_or_none(
            guild__id=ctx.guild.id, trigger=trigger
        )
        if record:
            record.enabled = is_enabled
            await record.save(update_fields=["enabled"])
            if is_enabled:
                await ctx.send(f"The autoresponse `{trigger}` has been enabled!")
            elif not is_enabled:
                await ctx.send(f"The autoresponse `{trigger}` has been disabled!")
                return
        else:
            raise AutoResponseDoesNotExist()

    @autoresponse.command(name="add", aliases=["addresponses", "addautoresponses"])
    async def autoresponse_add(self, ctx: commands.Context):
        """Add new autoresponse"""
        guild = await GuildModel.from_context(ctx)
        prompts = [
            Prompt("Triggered With", description="What shall be the trigger?"),
            Prompt(
                "Reacts With",
                description="What shall be the response?",
                out_type=str,
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

        trigger, response = await wizard.run(ctx.channel)

        record, _ = await AutoResponseModel.get_or_create(
            guild=guild, trigger=trigger.lower()
        )
        record.enabled = True
        record.response = response

        await record.save(update_fields=["enabled", "response"])

    @autoresponse.command(name="delete", aliases=["delresponse", "del"])
    @commands.has_permissions(administrator=True)
    async def autoresponse_delete(self, ctx: commands.Context, command: str):
        """Deletes the autoresponse"""
        guild = await GuildModel.from_context(ctx)

        if not await AutoResponseModel.exists(guild=guild, trigger=command):
            raise AutoResponseDoesNotExist()

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

        if not response:
            return

        await AutoResponseModel.get(guild=guild, trigger=command).delete()

    @autoresponse.command(name="list", aliases=["show", "showall", "all"])
    async def autoresponse_list(self, ctx):
        """Shows the list of all the autoresponses"""

        # Gets the list of all the enabled autoresponses in that guild!
        datas = await AutoResponseModel.filter(guild__id=ctx.guild.id)
        enabled_autoresponses = []
        disabled_autoresponses = []

        # Loops throught the list(datas) to get the enabled triggers for that server
        for data in datas:
            if data.enabled:
                enabled_autoresponses.append(f"`{data.trigger}`")
            else:
                disabled_autoresponses.append(f"`{data.trigger}`")

        # Creates the list into a string
        enabled_autoresponses = ", ".join(enabled_autoresponses)
        disabled_autoresponses = ", ".join(disabled_autoresponses)

        # Sends the embed with all the enabled autoresponses for that server!
        e = discord.Embed(title="Autorespones", colour=discord.Color.gold())

        e.add_field(
            name="Enabled Autoresponses",
            value=enabled_autoresponses
            if enabled_autoresponses
            else "There are no enabled autoresponses in this server!",
            inline=False,
        )

        if disabled_autoresponses:
            e.add_field(
                name="Disabled Autoresponses",
                value=disabled_autoresponses,
                inline=False,
            )
        e.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(AutoResponses(bot))
