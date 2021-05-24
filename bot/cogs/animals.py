import aiohttp
import discord
from discord.ext import commands

from bot.bot import PeaceBot
from bot.utils.mixins.better_cog import BetterCog


class Animals(BetterCog):
    @commands.command(aliases=["puppy", "pup"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def dog(self, ctx: commands.Context):
        async with aiohttp.ClientSession() as cs:
            async with cs.get("https://dog.ceo/api/breeds/image/random") as r:
                data = await r.json()
                image = data.get("message")
        embed = discord.Embed(title="Henlo")
        embed.set_image(url=image)
        embed.set_footer(text="https://dog.ceo/")
        await ctx.reply(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def fox(self, ctx: commands.Context):
        async with aiohttp.ClientSession() as cs:
            async with cs.get("https://randomfox.ca/floof/") as r:
                data = await r.json()
                image = data.get("image")
        embed = discord.Embed(title="What does the fox say?")
        embed.set_image(url=image)
        embed.set_footer(text="https://randomfox.ca")
        await ctx.reply(embed=embed)


def setup(bot: PeaceBot):
    bot.add_cog(Animals(bot))
