import json
import random

import aiohttp
import discord
from discord import Member
from discord.ext import commands
from discord.ext.commands import BucketType, Greedy


class Fun(commands.Cog):
    def __init__(self, bot):
        """Actual Fun Commands"""

        self.bot = bot

        # Opens the json file where the gifs are situated!
        with open("bot/data/funcommands.json", "r") as json_file:
            self.links = json.load(json_file)

        # Declaring the variables using data from json file.
        self.hugs = self.links["hugs"]
        self.slaps = self.links["slaps"]
        self.kills = self.links["kills"]
        self.pats = self.links["pats"]
        self.licks = self.links["licks"]

    @commands.command()
    @commands.guild_only()
    async def poptart(self, ctx: commands.Context, target: Greedy[Member]):
        """Throws a poptart at a user"""

        number_of_targets = len(target)
        speed_of_light = 299792458
        rand_percentage = random.random()
        percentage_of_speed = speed_of_light * rand_percentage
        if number_of_targets == 1:
            formatted_targets = target[0].mention
        elif number_of_targets == 2:
            formatted_targets = f"{target[0].mention} and {target[1].mention}"
        else:
            comma_separated = ", ".join(map(lambda m: m.mention, target[:-1]))
            final_element = f", and {target[-1].mention}"
            formatted_targets = f"{comma_separated}{final_element}"
        await ctx.send(
            f"{ctx.author.display_name} throws a poptart at {formatted_targets} with a mind numbing speed of "
            f"{int(percentage_of_speed)} m/s, that's {rand_percentage * 100:.2f}% the speed of light!"
        )

    @commands.command()
    @commands.guild_only()
    async def hug(self, ctx: commands.Context, member: discord.Member = None):
        embed = discord.Embed(
            description=f"{ctx.author.mention} hugged {member.mention}"
            if member
            else f"{ctx.author.mention} got hugged!",
            color=discord.Color.green(),
        )
        random_link = random.choice(self.hugs)
        embed.set_image(url=random_link)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def pat(self, ctx: commands.Context, member: discord.Member = None):
        embed = discord.Embed(
            description=f"{ctx.author.mention} pats {member.mention}"
            if member
            else f"{ctx.author.mention} got patted!",
            color=discord.Color.green(),
        )
        random_link = random.choice(self.pats)
        embed.set_image(url=random_link)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def kill(self, ctx: commands.Context, member: discord.Member = None):
        embed = discord.Embed(
            description=f"{ctx.author.mention} KILLED {member.mention}"
            if member
            else f"{ctx.author.mention} is a murdurer!",
            color=discord.Color.red(),
        )
        random_link = random.choice(self.kills)
        embed.set_image(url=random_link)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def slap(self, ctx: commands.Context, member: discord.Member = None):
        embed = discord.Embed(
            description=f"{ctx.author.mention} slapped {member.mention}"
            if member
            else f"{ctx.author.mention} slapped!",
            color=discord.Color.red(),
        )
        random_link = random.choice(self.slaps)
        embed.set_image(url=random_link)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def lick(self, ctx: commands.Context, member: discord.Member = None):
        embed = discord.Embed(
            description=f"{ctx.author.mention} licked {member.mention}"
            if member
            else f"{ctx.author.mention} got licked!",
            color=discord.Color.red(),
        )
        random_link = random.choice(self.licks)
        embed.set_image(url=random_link)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Fun(bot))
