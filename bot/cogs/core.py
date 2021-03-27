from discord import Color, Embed, NotFound
from discord.ext import commands

from models import GuildModel


class MessageNotRefrenced(commands.CommandError):
    def __str__(self):
        return "Please reply to the valid message you want to re-run!"


class Core(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=["latency"])
    async def ping(self, ctx: commands.Context):
        """Check latency of the bot"""
        latency = str(round(self.bot.latency * 1000, 1))
        await ctx.send(
            embed=Embed(title="Pong!", description=f"{latency}ms", color=Color.blue())
        )

    @commands.command(aliases=["statistics"])
    async def stats(self, ctx: commands.Context):
        """Stats of the bot"""
        users = len(self.bot.users)
        guilds = len(self.bot.guilds)

        embed = Embed(color=Color.dark_green())
        embed.add_field(name="Guilds", value=guilds)
        embed.add_field(name="Users", value=users)
        embed.set_thumbnail(url=ctx.guild.me.avatar_url)

        await ctx.send(embed=embed)

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
        await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx: commands.Context):
        """Get the invite link of this bot from this command!"""
        await ctx.send(
            f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot"
        )


def setup(bot: commands.Bot):
    bot.add_cog(Core(bot))
