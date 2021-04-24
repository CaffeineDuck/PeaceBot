import discord
from discord.ext import commands

from bot.bot import PeaceBot
from bot.utils.cached_reddit import RedditPostCacher


class Reddit(commands.Cog):
    def __init__(self, bot: PeaceBot):
        self.bot = bot
        self.subreddits = ("aww", "memes", "cursedcomments")
        self.cache = RedditPostCacher(self.subreddits, "cache/Reddit.pickle")
        self.cache.cache_posts.start()

    @commands.command(aliases=["memes"])
    async def meme(self, ctx: commands.Context):
        await self.cache.reddit_sender(ctx, "memes")

    @commands.command()
    async def aww(self, ctx: commands.Context):
        await self.cache.reddit_sender(ctx, "aww")

    @commands.command(aliases=["cursedcomments"])
    async def cursed(self, ctx: commands.Context):
        await self.cache.reddit_sender(ctx, "cursedcomments")


def setup(bot: PeaceBot):
    bot.add_cog(Reddit(bot))
