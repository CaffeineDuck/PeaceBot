import discord
from discord.ext import commands
from discord.ext.commands import BucketType

from models import AutoResponseModel, GuildModel
from bot.utils.wizard_embed import Prompt, Wizard


class AutoResponseDoesNotExist(commands.CommandError):
    def __str__(self):
        return "This autoresponse doesnot in this guild!"


class AutoResponses(commands.Cog):
    """Manage the autoresponses in this server"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.defualt_responses = ["imagine"]

    # Checks if the autoresponse is enabled and exists in that server!
    async def commands_checker(self, command, guild_id):
        return await AutoResponseModel.exists(
            guild__id=guild_id, trigger=command, enabled=True
        )

    # On message listner to give the autoresponse if it matches the trigger!
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        # Loops through all the custom autoresponses (GUILD SPECIFIC)
        guild = await GuildModel.from_guild_object(msg.guild)
        autoresponses = await AutoResponseModel.filter(guild=guild)
        ctx: commands.Context = await self.bot.get_context(msg)
        for data in autoresponses:
            if data.is_command:
                try:
                if (guild.prefix + data.trigger) == msg.content:
                    await msg.channel.send(data.response)
                    return
            elif msg.content.lower() == data.trigger:
                await msg.channel.send(data.response)
                return

        # It checks the if the prebaked autoresponses are enabled in that server!
        try:
            if "imagine" in msg.content.split()[0] and await self.commands_checker(
                "imagine", msg.guild.id
            ):
                await msg.channel.send(f"I can't even {msg.content}, bro!")
        except IndexError:
            pass

    @commands.group(aliases=["autoresponses"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def autoresponse(self, ctx: commands.Context):
        """Configure Autoresponses"""
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @autoresponse.command(aliases=["change"])
    async def toggle(self, ctx: commands.Context, trigger: str, is_enabled: bool):
        """Enable/ Disable an autoresponse!"""

        if trigger.lower() in self.defualt_responses:
            record = (
                await AutoResponseModel.get_or_create(
                    guild__id=ctx.guild.id, trigger=trigger
                )
            )[0]
            record.enabled = is_enabled
            await record.save(update_fields=["enabled"])

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
            Prompt("Reacts With", description="What shall be the response?"),
            Prompt(
                "Is Command",
                description="Should the autoresponse only be usable after using prefix?",
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

        trigger, response, is_command = await wizard.run(ctx.channel)

        record, _ = await AutoResponseModel.get_or_create(
            guild=guild, trigger=trigger.lower()
        )
        record.enabled = True
        record.response = response
        record.is_command = is_command

        await record.save(update_fields=["enabled", "response", "is_command"])

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
