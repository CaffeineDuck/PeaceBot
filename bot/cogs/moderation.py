import asyncio
import json
import os

from datetime import datetime, timedelta

import discord

from discord.ext import commands
from discord.ext.commands import (
    has_permissions,
    BucketType,
    cooldown,
    bot_has_permissions,
    command,
    guild_only,
)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def create_muted_role(self, ctx: commands.Context):
        await ctx.guild.create_role(
            name="Muted",
            permissions=discord.Permissions(send_messages=False, read_messages=True),
        )
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        return role

    @command(aliases=["m"])
    @guild_only()
    @cooldown(1, 10, BucketType.user)
    @has_permissions(manage_roles=True)
    async def mute(self, ctx: commands.Context, user: discord.Member = None):
        """
        Mutes the specified user
        """
        role = discord.utils.get(
            ctx.guild.roles, name="Muted"
        ) or await self.create_muted_role(ctx)

        await user.add_roles(role)

        embed = discord.Embed(description="Has been muted!", color=discord.Color.gold())
        embed.set_author(name=user, url=user.avatar_url, icon_url=user.avatar_url)
        await ctx.send(embed=embed, delete_after=5)

    @command()
    @guild_only()
    @has_permissions(manage_roles=True)
    @bot_has_permissions(manage_roles=True)
    async def unmute(self, ctx, user: discord.Member):
        """
        Unmutes the specified user
        """
        role = discord.utils.get(ctx.guild.roles, name="Muted")

        embed = discord.Embed(
            description="Has been unmuted!"
            if role in user.roles
            else "Hasn't been muted yet!"
        )
        embed.set_author(name=user, url=user.avatar_url, icon_url=user.avatar_url)
        await ctx.send(embed=embed, delete_after=5)

        # TODO: Use a try/ except statement here!
        await user.remove_roles(role)

    @command(name="kick")
    @guild_only()
    @cooldown(1, 60, BucketType.user)
    @has_permissions(kick_members=True)
    @bot_has_permissions(kick_members=True)
    async def kick_member(
        self, ctx, user: discord.Member, *, reason="No Reason Specified"
    ):
        """
        Kicks the user from the server
        """
        await user.kick(reason=reason)
        embed = discord.Embed(
            description=f"Reason: {reason}", color=discord.Color.red()
        )
        embed.set_author(
            name=user,
            url=user.avatar_url,
            icon_url=user.avatar_url,
        )
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)
        await user.send(f"You have been kicked. Reason {reason}")

    @command(name="purge")
    @guild_only()
    @cooldown(1, 10, BucketType.user)
    @has_permissions(manage_messages=True)
    @bot_has_permissions(manage_messages=True)
    async def purge_messages(self, ctx, num_messages: int = 10):
        """
        Delete messages from current channel
        """
        channel = ctx.message.channel
        await ctx.message.delete()
        deleted_messages = len(await channel.purge(limit=num_messages))
        await ctx.send(
            f"`{deleted_messages} messages has been deleted!`", delete_after=5
        )

    @command(name="lock")
    @guild_only()
    @cooldown(1, 10, BucketType.user)
    @has_permissions(manage_channels=True)
    @bot_has_permissions(manage_channels=True)
    async def lock_channel(self, ctx, channel: discord.TextChannel = None):
        """
        Makes typing in the channel unaccessible to everyone except for admins
        """
        channel = channel or ctx.channel

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False)
        }
        await channel.edit(overwrites=overwrites)
        await ctx.send(
            "**The channel `{ctx.channel.name}` has successfully been locked!**"
        )

    @command(name="unlock")
    @guild_only()
    @cooldown(1, 10, BucketType.user)
    @has_permissions(manage_channels=True)
    @bot_has_permissions(manage_channels=True)
    async def unlock_channel(self, ctx, channel: discord.TextChannel = None):
        """
        Makes the chat acessible to everyone as before locking
        """
        channel = channel or ctx.channel

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(send_messages=True)
        }
        await channel.edit(overwrites=overwrites)
        await ctx.send(
            "**The channel `{channel.name}` has successfully been unlocked!**"
        )


def setup(bot):
    bot.add_cog(Moderation(bot))
