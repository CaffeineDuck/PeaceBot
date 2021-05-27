import os
from typing import Optional, Union

import discord
from discord.ext import commands
from discord.ext.commands import BucketType

from bot.bot import PeaceBot
from bot.utils.mixins.better_cog import BetterCog
from models import CommandModel, GuildModel


class CommandToggleError(commands.CommandError):
    pass


# TODO: Make the command's role/perms customizable
class Config(BetterCog):
    """
    Configure the bot for your guild using the
    commands in this extension.
    """

    @commands.command()
    @commands.cooldown(1, 10, BucketType.user)
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def changeprefix(self, ctx: commands.Context, prefix: str):
        guild = await GuildModel.from_context(ctx)
        guild.prefix = prefix
        await guild.save(update_fields=["prefix"])
        self.bot.prefixes_cache[ctx.guild.id] = prefix

        embed = discord.Embed(
            color=discord.Color.blue(),
            description=f"I set your guild's prefix to `{guild.prefix}`",
        )
        await ctx.reply(embed=embed)

    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.command(name="isdisabled")
    async def is_disabled(
        self,
        ctx: commands.Context,
        command: str,
        channel: Optional[discord.TextChannel],
    ):
        channel = channel or ctx.channel
        record = await CommandModel.get_or_none(
            guild__id=ctx.guild.id, name=command, channel=channel.id
        )

        if not record or record.enabled:
            await ctx.reply(f"`{command}` is enabled in {channel.mention}")
        else:
            await ctx.reply(f"`{command}` is disabled in {channel.mention}")

        await ctx.send(
            "Note that this only shows the commands that were disabled manully,"
            + " commands that were automatically disabled due to a command group being"
            + " disabled, won't be shown here as disabled!"
        )

    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @commands.command()
    async def disable(
        self,
        ctx: commands.Context,
        command: str,
        channel: Optional[Union[discord.TextChannel, str]],
    ):
        await self.command_enable_disable_handler(ctx, command, channel, False)

    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @commands.command()
    async def enable(
        self,
        ctx: commands.Context,
        command: str,
        channel: Optional[Union[discord.TextChannel, str]],
    ):
        await self.command_enable_disable_handler(ctx, command, channel, True)

    async def command_enable_disable_handler(
        self,
        ctx: commands.Context,
        command: str,
        channel: Optional[Union[discord.TextChannel, str]],
        toggle: bool,
    ):
        channel = channel or ctx.channel
        channels = ctx.guild.channels + ["all"]
        if channel not in channels:
            raise commands.ChannelNotFound(channel)

        full_command = self.bot.get_command(command)

        if not full_command:
            full_command = self.bot.get_cog(command)
            is_cog = True
        else:
            is_cog = False

        if not full_command:
            raise CommandToggleError(f"Command {command} not found!")

        if full_command in self.get_commands() or command in ["core", "config"]:
            raise CommandToggleError("You can't enable/disable the core commands!")

        valid_channels = ctx.guild.text_channels if channel == "all" else [ctx.channel]

        guild = self.bot.guilds_cache.get(ctx.guild.id)

        for text_channel in valid_channels:
            record, _ = await CommandModel.get_or_create(
                guild=guild,
                name=full_command.qualified_name if is_cog else full_command.name,
                channel=text_channel.id,
            )
            record.is_cog = is_cog
            record.enabled = toggle
            await record.save()

        # Clearing the cache
        self.bot.commands_cache[ctx.guild.id] = None

        toggle_str = "enabled" if toggle else "disabled"
        await ctx.reply(f"`{command}` has been {toggle_str} for `{channel}`!")


def setup(bot: PeaceBot):
    bot.add_cog(Config(bot))
