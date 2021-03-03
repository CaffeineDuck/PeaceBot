import pickle
import random
import traceback

import aiofiles
import asyncpraw
import discord
from discord.ext import commands, tasks

from bot.utils.cached_reddit import RedditPostCacher


class NSFW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.subreddits = (
            "ass",
            "LegalTeens",
            "boobs",
            "pussy",
            "TooCuteForPorn",
            "Nudes",
            "cumsluts",
            "porngifs",
            "hentai",
        )
        self.cache = RedditPostCacher(self.subreddits, "cache/NSFW.pickle")
        self.cache.cache_posts.start()

    async def _reddit_sender(self, ctx, subrd: str, title: str):
        """Fetches from reddit and sends results

        Parameters
        ----------
        ctx : discord.ext.commands.Context
                The invocation context
        subrd : str
                The subreddit to fetch from
        title : str
                The title to use in the embed
        """
        # Gets the data from reddit!
        submission = await self.cache.get_random_post(subrd)

        # Sends the embed!
        embed = discord.Embed(
            title=title,
            timestamp=ctx.message.created_at,
            colour=discord.Color.dark_purple(),
        )
        embed.set_image(url=submission)
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

    # Errorhandler, if the channel isn't NSFW!
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.NSFWChannelRequired):
            image = "https://i.imgur.com/oe4iK5i.gif"
            embed = discord.Embed(
                title="NSFW not allowed here",
                description="Use NSFW commands in a NSFW marked channel.",
                color=discord.Color.dark_blue(),
            )
            embed.set_image(url=image)
            await ctx.send(embed=embed)

    # NSFW COMMANDS
    @commands.command()
    @commands.is_nsfw()
    async def ass(self, ctx):
        await self._reddit_sender(ctx, "ass", "DRUMS")

    @commands.command()
    @commands.is_nsfw()
    async def grool(self, ctx):
        await self._reddit_sender(ctx, "grool", "Dat Pussy Juice 😋")

    @commands.command()
    @commands.is_nsfw()
    async def teen(self, ctx):
        await self._reddit_sender(ctx, "LegalTeens", "You like them young?")

    @commands.command()
    @commands.is_nsfw()
    async def boobs(self, ctx):
        await self._reddit_sender(ctx, "boobs", "Bounce! Bounce!")

    @commands.command()
    @commands.is_nsfw()
    async def pussy(self, ctx):
        await self._reddit_sender(ctx, "pussy", "Wet or Dry?")

    @commands.command()
    @commands.is_nsfw()
    async def cutesluts(self, ctx):
        await self._reddit_sender(
            ctx, "TooCuteForPorn", "Too cute for porn, aren't they?"
        )

    @commands.command()
    @commands.is_nsfw()
    async def nudes(self, ctx):
        await self._reddit_sender(ctx, "Nudes", "Sick of pornstars? Me too!")

    @commands.command(aliases=["cumsluts"])
    @commands.is_nsfw()
    async def cum(self, ctx):
        await self._reddit_sender(ctx, "cumsluts", "And they don't stop cumming!")

    @commands.command()
    @commands.is_nsfw()
    async def hentai(self, ctx):
        await self._reddit_sender(ctx, "hentai", "AnImE iS jUsT CaRtOoN")


def setup(bot):
    bot.add_cog(NSFW(bot))
