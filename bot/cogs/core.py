import platform
import sys

import psutil
from bot.bot import PeaceBot
import discord
from discord import Color, Embed, NotFound
from discord import __version__ as discord_version
from discord.ext import commands

from models import GuildModel, CommandModel

from typing import Optional, Union


class CommandToggleError(commands.CommandError):
    pass


class MessageNotRefrenced(commands.CommandError):
    def __str__(self):
        return "Please reply to the valid message you want to re-run!"


class Core(commands.Cog):
    def __init__(self, bot: PeaceBot):
        self.bot = bot

    @commands.command(aliases=["latency"])
    async def ping(self, ctx: commands.Context):
        """Check latency of the bot"""
        latency = str(round(self.bot.latency * 1000, 1))
        await ctx.reply(
            embed=Embed(title="Pong!", description=f"{latency}ms", color=Color.blue())
        )

    @commands.command(aliases=["statistics"])
    async def stats(self, ctx: commands.Context):
        """Stats of the bot"""
        users = len(self.bot.users)
        guilds = len(self.bot.guilds)

        embed = Embed(color=Color.dark_green())
        fields = (
            ("Guilds", guilds),
            ("Users", users),
            (
                "Memory",
                "{:.4} MB".format(psutil.Process().memory_info().rss / 1024 ** 2),
            ),
            ("Python version", ".".join([str(v) for v in sys.version_info[:3]])),
            ("DPY Version", discord_version),
        )
        for name, value in fields:
            embed.add_field(name=name, value=str(value), inline=False)

        embed.set_thumbnail(url=str(ctx.guild.me.avatar_url))

        await ctx.reply(embed=embed)

    @commands.command(aliases=["re"])
    async def redo(self, ctx: commands.Context):
        """
        Reply to a message to rerun it if its a command, helps when you've made typos
        """
        ref = ctx.message.reference
        if not ref:
            raise MessageNotRefrenced()
        try:
            message = await ctx.channel.fetch_message(ref.message_id)
        except NotFound:
            return await ctx.reply("Couldn't find that message")
        if message.author != ctx.author:
            return
        await self.bot.process_commands(message)

    @commands.command()
    @commands.guild_only()
    async def prefix(self, ctx: commands.Context):
        """
        Use this command to find out the prefix of this bot in your guild
        """
        guild = await GuildModel.from_context(ctx)
        prefix = guild.prefix
        embed = Embed(
            color=Color.blue(),
            description=f"{ctx.author.mention}, My current prefix is `{prefix}` or {self.bot.user.mention}",
        )
        await ctx.reply(embed=embed)

    @commands.command()
    async def invite(self, ctx: commands.Context):
        """Get the invite link of this bot from this command!"""
        await ctx.reply(
            f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot"
        )

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

        if full_command in self.get_commands() or command == "core":
            raise CommandToggleError("You can't enable/disable the core commands!")

        valid_channels = ctx.guild.text_channels if channel == "all" else [ctx.channel]

        guild = await GuildModel.get(id=ctx.guild.id)

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
    bot.add_cog(Core(bot))
