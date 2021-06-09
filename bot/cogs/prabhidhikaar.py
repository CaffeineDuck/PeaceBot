import asyncio
import discord
from discord.ext import commands

from bot.bot import PeaceBot
from bot.cogs.events.last_to_leave_vc import LastToLeaveVc
from bot.utils.mixins.better_cog import BetterCog
from bot.utils.botuser import BotUser

PRABHIDHIKAAR_GUILD_ID = 836230453622341663
BOT_TESTING_INFO = {
    "channel": 852184824756174939,
    "bot-entries": 852192052083294228,
    "terms": "By requesting to add your bot, you must agree to the guidelines presented in the <#852184861707862036>.",
    "role": 852204987127300168,
    "test-guild": 852268585786671125,
}


class Prabhidhikaar(BetterCog):
    def cog_check(self, ctx: commands.Context):
        if ctx.guild.id == PRABHIDHIKAAR_GUILD_ID:
            return True
        return False

    def cog_help_check(self, ctx: commands.Context):
        if ctx.guild.id == PRABHIDHIKAAR_GUILD_ID:
            return True
        return False

    @commands.group(name="loadevent", invoke_without_command=True)
    async def load_event(self, ctx: commands.Context):
        await ctx.send_help(ctx.command)

    @load_event.command(name="ltlvc")
    async def load_last_to_leave_vc(self, ctx: commands.Context):
        self.bot.add_cog(LastToLeaveVc(self.bot))
        await ctx.send("Last to leave vc has been loaded!")

    @commands.group(name="unloadevent", invoke_without_command=True)
    async def unload_event(self, ctx: commands.Context):
        await ctx.send_help(ctx.command)

    @unload_event.command(name="ltlvc")
    async def unload_last_to_leave_vc(self, ctx: commands.Context):
        self.bot.remove_cog("LastToLeaveVc")

    @commands.command()
    @commands.cooldown(1, 600, commands.BucketType.user)
    @commands.has_any_role("Server Booster", "Kilo Chad 10+")
    async def addbot(self, ctx, user_id: BotUser, *, reason: str):
        """Requests your bot to be added to the server.
        To request your bot you must pass your bot's user ID and a reason
        You will get a DM regarding the status of your bot, so make sure you
        have them on.
        """

        info = BOT_TESTING_INFO
        confirm = None

        def terms_acceptance(msg):
            nonlocal confirm
            if msg.author.id != ctx.author.id:
                return False
            if msg.channel.id != ctx.channel.id:
                return False
            if msg.content in ("**I agree**", "I agree"):
                confirm = True
                return True
            elif msg.content in ("**Abort**", "Abort"):
                confirm = False
                return True
            return False

        msg = (
            f'{info["terms"]}. Moderators reserve the right to kick or reject your bot for any reason.\n\n'
            "If you agree, reply to this message with **I agree** within 1 minute. If you do not, reply with **Abort**."
        )
        prompt = await ctx.send(msg)

        try:
            await self.bot.wait_for("message", check=terms_acceptance, timeout=60.0)
        except asyncio.TimeoutError:
            return await ctx.send("Took too long. Aborting.")
        finally:
            await prompt.delete()

        if not confirm:
            return await ctx.send("Aborting.")

        url = f"https://discord.com/oauth2/authorize?client_id={user_id.id}&scope=bot&guild_id={ctx.guild.id}"
        url2 = f"https://discord.com/oauth2/authorize?client_id={user_id.id}&scope=bot&guild_id={info.get('test-guild')}"

        description = f"{reason}\n\n[Invite URL]({url})\n[Test Invite URL]({url2})"
        embed = discord.Embed(
            title="Bot Request",
            colour=discord.Colour.blurple(),
            description=description,
        )
        embed.add_field(
            name="Author", value=f"{ctx.author} (ID: {ctx.author.id})", inline=False
        )
        embed.add_field(name="Bot", value=f"{user_id} (ID: {user_id.id})", inline=False)
        embed.timestamp = ctx.message.created_at

        # data for the bot to retrieve later
        embed.set_footer(text=ctx.author.id)
        embed.set_author(name=user_id.id, icon_url=user_id.avatar_url_as(format="png"))

        channel = ctx.guild.get_channel(info["bot-entries"])
        try:
            msg = await channel.send(embed=embed)
            await msg.add_reaction("\N{WHITE HEAVY CHECK MARK}")
            await msg.add_reaction("\N{CROSS MARK}")
            await msg.add_reaction("\N{NO ENTRY SIGN}")
        except discord.HTTPException as e:
            return await ctx.send(
                f"Failed to request your bot somehow. Tell Sussy, {str(e)!r}"
            )

        await ctx.send(
            "Your bot has been requested to the moderators. I will DM you the status of your request."
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id != PRABHIDHIKAAR_GUILD_ID:
            return

        emoji = str(payload.emoji)
        if emoji not in (
            "\N{WHITE HEAVY CHECK MARK}",
            "\N{CROSS MARK}",
            "\N{NO ENTRY SIGN}",
        ):
            return

        channel_id = BOT_TESTING_INFO["bot-entries"]
        if payload.channel_id != channel_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        try:
            message = await channel.fetch_message(payload.message_id)
        except (AttributeError, discord.HTTPException):
            return

        if len(message.embeds) != 1:
            return

        embed = message.embeds[0]
        # Already been handled.
        if embed.colour != discord.Colour.blurple():
            return

        user = await self.bot.get_or_fetch_member(guild, payload.user_id)
        if user is None or user.bot:
            return

        author_id = int(embed.footer.text)
        bot_id = embed.author.name
        if emoji == "\N{WHITE HEAVY CHECK MARK}":
            to_send = f"Your bot, <@{bot_id}>, has been added to {channel.guild.name}."
            colour = discord.Colour.dark_green()
        elif emoji == "\N{NO ENTRY SIGN}":
            to_send = (
                f"Your bot, <@{bot_id}>, could not be added to {channel.guild.name}.\n"
                "This could be because it was private or required code grant. "
                "Please make your bot public and resubmit your application."
            )
            colour = discord.Colour.orange()
        else:
            to_send = (
                f"Your bot, <@{bot_id}>, has been rejected from {channel.guild.name}."
            )
            colour = discord.Colour.dark_magenta()

        member = await self.bot.get_or_fetch_member(guild, author_id)
        try:
            await member.send(to_send)
        except (AttributeError, discord.HTTPException):
            colour = discord.Colour.gold()

        embed.add_field(
            name="Responsible Moderator", value=f"{user} (ID: {user.id})", inline=False
        )
        embed.colour = colour
        await self.bot.http.edit_message(
            payload.channel_id, payload.message_id, embed=embed.to_dict()
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != PRABHIDHIKAAR_GUILD_ID:
            return

        if not member.bot:
            return

        role = member.guild.get_role(BOT_TESTING_INFO.get("role"))
        await member.add_roles(role)


def setup(bot: PeaceBot):
    bot.add_cog(Prabhidhikaar(bot))
