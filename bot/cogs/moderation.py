import asyncio
import json
import os

from datetime import datetime, timedelta

import discord

from discord.ext import commands
from discord.ext.commands import has_permissions, BucketType, cooldown


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["m"])
    @cooldown(1, 10, BucketType.user)
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, user: discord.Member = None, time: int = None):
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            await ctx.guild.create_role(
                name="Muted",
                permissions=discord.Permissions(
                    send_messages=False, read_messages=True
                ),
            )
            role = discord.utils.get(ctx.guild.roles, name="Muted")
        await user.add_roles(role)

        embed = discord.Embed(
            description=f"Has been muted for {time} minutes!"
            if time
            else "Has been muted!"
        )
        embed.set_author(name=user, url=user.avatar_url, icon_url=user.avatar_url)
        await ctx.send(embed=embed, delete_after=5)

        if not time:
            return

        await asyncio.sleep(time * 60)
        await user.remove_roles(role)
        embed = discord.Embed(description=f"Has been unmuted after {time} minutes!")
        embed.set_author(name=user, url=user.avatar_url, icon_url=user.avatar_url)
        await ctx.send(embed=embed, delete_after=5)

    @commands.command(aliases=["um"])
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, user: discord.Member):
        role = discord.utils.get(ctx.guild.roles, name="Muted")

        embed = discord.Embed(
            description="Has been unmuted!"
            if role in user.roles
            else "Hasn't been muted yet!"
        )
        embed.set_author(name=user, url=user.avatar_url, icon_url=user.avatar_url)
        await ctx.send(embed=embed, delete_after=5)
        await user.remove_roles(role)

    @commands.command(aliases=["k"])
    @cooldown(1, 60, BucketType.user)
    @has_permissions(kick_members=True)
    async def kick(
        self, ctx, user: discord.Member = None, *, reason="No Reason Specified"
    ):
        if not user:
            await ctx.send("Please specify whom to kick!")
        else:
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

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="purge")
    async def purge(self, ctx, num_messages: int = 10, user: discord.Member = None):
        """
        Delete messages from current channel
        """
        if user:
            channel = ctx.message.channel

            def check(msg):
                return msg.author.id == user.id

            await ctx.message.delete()
            await channel.purge(limit=num_messages, check=check, before=None)
            await ctx.send(
                f"`{num_messages} messages from {user} deleted!`", delete_after=5
            )
            return
        channel = ctx.message.channel
        await ctx.message.delete()
        await channel.purge(limit=num_messages, check=None, before=None)
        await ctx.send(f"`{num_messages} messages has been deleted!`", delete_after=5)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel

        if ctx.guild.default_role not in channel.overwrites:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False)
            }
            await channel.edit(overwrites=overwrites)
            await ctx.send(
                "**The channel `{ctx.channel.name}` has successfully been locked!**"
            )
        elif (
            channel.overwrites[ctx.guild.default_role].send_messages == True
            or channel.overwrites[ctx.guild.default_role].send_messages == None
        ):
            overwrites = channel.overwrites[ctx.guild.default_role]
            overwrites.send_messages = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
            await ctx.send(
                "**The channel `{ctx.channel.name}` has successfully been locked!**"
            )
        else:
            overwrites = channel.overwrites[ctx.guild.default_role]
            overwrites.send_messages = True
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
            await ctx.send(
                f"**The channel `{ctx.channel.name}` has now been unlocked!**"
            )


def setup(bot):
    bot.add_cog(Moderation(bot))
