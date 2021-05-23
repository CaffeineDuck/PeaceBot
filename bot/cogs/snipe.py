from datetime import datetime

from cachetools import TTLCache
from discord import Color, Embed
from discord.ext import commands

from bot.utils.mixins.better_cog import BetterCog
from discord.ext.commands import BucketType


class NoSnipeableMessage(commands.CommandError):
    def __str__(self):
        return "There aren't any recent message that have been deleted/ edited!"


class Snipe(BetterCog):
    def __init__(self, bot, *args, **kwargs):
        self.bot = bot
        self.delete_snipes = TTLCache(100, 600)
        self.edit_snipes = TTLCache(100, 600)
        super().__init__(bot)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        self.delete_snipes[message.channel] = message

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return

        self.edit_snipes[after.channel] = (before, after)

    @commands.group(name="snipe")
    @commands.cooldown(1, 5, BucketType.user)
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True, read_messages=True)
    async def snipe_group(self, ctx):
        """Snipe a deleted message"""
        if ctx.invoked_subcommand is None:
            try:
                sniped_message = self.delete_snipes[ctx.channel]
            except KeyError:
                raise NoSnipeableMessage()
            else:
                result = Embed(
                    color=Color.red(),
                    description=sniped_message.content,
                    timestamp=sniped_message.created_at,
                )
                result.set_author(
                    name=sniped_message.author.display_name,
                    icon_url=sniped_message.author.avatar_url,
                )
                await ctx.reply(embed=result)

    @snipe_group.command(name="edit")
    async def snipe_edit(self, ctx):
        """Snipes an edited message"""
        try:
            before, after = self.edit_snipes[ctx.channel]
        except KeyError:
            raise NoSnipeableMessage()
        else:
            result = Embed(color=Color.red(), timestamp=after.edited_at)
            result.add_field(name="Before", value=before.content, inline=False)
            result.add_field(name="After", value=after.content, inline=False)
            result.set_author(
                name=after.author.display_name, icon_url=after.author.avatar_url
            )
            await ctx.reply(embed=result)


def setup(bot, *args, **kwargs):
    bot.add_cog(Snipe(bot, *args, **kwargs))
