import re
from asyncio import Event

import aiohttp
from __main__ import PeaceBot
from discord import Color, Embed, HTTPException, Message, PartialEmoji
from discord.ext import commands

from bot.utils.mixins.better_cog import BetterCog
from discord.ext.commands import BucketType, Greedy


class Emoji(BetterCog):
    def __init__(self, bot: PeaceBot):
        self.bot = bot
        self.emoji_extraction_pattern = re.compile(r"<(a?):([a-zA-Z0-9\_]+):([0-9]+)>")
        super().__init__(bot)

    @commands.group(name="thieve", aliases=["steal"], invoke_without_command=True)
    async def thieve_group(self, ctx: commands.Context):
        """Steal"""
        await ctx.send_help(ctx.command)

    async def extract_emoji_from_messages(self, messages):
        parsed_emoji = set()
        for message in messages:
            for match in self.emoji_extraction_pattern.finditer(message.content):
                animated = bool(match.group(1))
                name = match.group(2)
                emoji_id = int(match.group(3))
                emoji = PartialEmoji.with_state(
                    self.bot._connection, animated=animated, name=name, id=emoji_id
                )
                parsed_emoji.add(emoji)
        return parsed_emoji

    async def copy_emoji_to_guild(self, emoji, guild):
        created_emoji = await guild.create_custom_emoji(
            name=emoji.name, image=await emoji.url.read()
        )
        return created_emoji

    def message_contains_emoji(self, message):
        match = self.emoji_extraction_pattern.search(message.content)
        return match is not None

    @commands.has_guild_permissions(manage_emojis=True)
    @thieve_group.command(name="emoji", aliases=["emote"])
    async def steal_emoji(
        self, ctx, emojis: Greedy[PartialEmoji], messages: Greedy[Message]
    ):
        """Steals an emoji"""
        if not emojis and not messages:
            last_message = [
                await ctx.history(limit=10).find(
                    lambda m: self.message_contains_emoji(m)
                )
            ]
            if None in last_message:
                last_message = []
            emojis = await self.extract_emoji_from_messages(last_message)
        elif messages:
            emojis = await self.extract_emoji_from_messages(messages)
        added_emoji = set()
        async with ctx.channel.typing():
            limit_reached = Event()
            for emoji in filter(lambda e: e.is_custom_emoji(), emojis):
                try:
                    created_emoji = await self.copy_emoji_to_guild(emoji, ctx.guild)
                    added_emoji.add(created_emoji)
                except HTTPException:
                    limit_reached.set()
                    break
        if added_emoji:
            summary = Embed(
                title="New emoji added ✅",
                description="\n".join(
                    f"\\:{emoji.name}\\: -> {emoji}" for emoji in added_emoji
                ),
                color=Color.green(),
            )
            if limit_reached.is_set():
                summary.description += (
                    "\nSome emoji were not added because you hit the limit."
                )
        elif not added_emoji and limit_reached.is_set():
            summary = Embed(
                title="Emoji limit reached ⛔",
                description="You have reached the max emoji for this server, get more boosts to raise this limit!",
                color=Color.red(),
            )
        else:
            messages_given = bool(messages)
            error_message = "message(s) given" if messages_given else "last 10 messages"
            summary = Embed(
                title="No emoji found 😔",
                description=f"No emoji were found in the {error_message}",
                color=Color.red(),
            )
        await ctx.reply(embed=summary)


def setup(bot: PeaceBot):
    bot.add_cog(Emoji(bot))
