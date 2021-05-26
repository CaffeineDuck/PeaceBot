from discord.ext import commands

from bot.utils.cached_reddit import RedditPostCacher
from bot.utils.mixins.better_cog import BetterCog


class NSFW(BetterCog):
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
            "hentai",
            "grool",
        )
        self.cache = RedditPostCacher(self.subreddits, "cache/NSFW.pickle")
        self.cache.cache_posts.start()
        super().__init__(bot)

    def cog_help_check(self, ctx: commands.Context):
        if not ctx.guild:
            return True
        if ctx.channel.is_nsfw():
            return True
        return False

    # NSFW COMMANDS
    @commands.command()
    @commands.is_nsfw()
    async def ass(self, ctx):
        """Booty Pics"""
        await self.cache.reddit_sender(ctx, "ass")

    @commands.command()
    @commands.is_nsfw()
    async def grool(self, ctx):
        """Pussy juice yum"""
        await self.cache.reddit_sender(ctx, "grool")

    @commands.command()
    @commands.is_nsfw()
    async def teen(self, ctx):
        """Pussy juice yum"""
        await self.cache.reddit_sender(ctx, "LegalTeens")

    @commands.command()
    @commands.is_nsfw()
    async def boobs(self, ctx):
        """Pussy juice yum"""
        await self.cache.reddit_sender(ctx, "boobs")

    @commands.command()
    @commands.is_nsfw()
    async def pussy(self, ctx):
        """I like cats"""
        await self.cache.reddit_sender(ctx, "pussy")

    @commands.command()
    @commands.is_nsfw()
    async def cutesluts(self, ctx):
        """HMMM"""
        await self.cache.reddit_sender(ctx, "TooCuteForPorn")

    @commands.command()
    @commands.is_nsfw()
    async def nudes(self, ctx):
        """Porn industry == bad, real peps == nice"""
        await self.cache.reddit_sender(ctx, "Nudes")

    @commands.command(aliases=["cumsluts"])
    @commands.is_nsfw()
    async def cum(self, ctx):
        """I am ~~cumming~~ coming"""
        await self.cache.reddit_sender(ctx, "cumsluts")

    @commands.command()
    @commands.is_nsfw()
    async def hentai(self, ctx):
        """When I die, don't cry, just look at the sky and say `I love hentai`"""
        await self.cache.reddit_sender(ctx, "hentai")


def setup(bot):
    bot.add_cog(NSFW(bot))
