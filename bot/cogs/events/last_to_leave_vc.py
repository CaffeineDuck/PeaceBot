import asyncio
import random
import re
from typing import List, Optional

import discord
from click import Option
from discord.ext import commands, tasks
from discord.permissions import PermissionOverwrite

from bot.bot import PeaceBot
from bot.utils.mixins.better_cog import BetterCog

PRABHIDHIKAAR_GUILD_ID = 836230453622341663

# Last to leave VC event!
LTLVC_EVENT_NAME = "Last To Leave VC"
LTLVC_EVENT_MANAGERS = [
    757454088416919552,
    775077885043146752,
    475196477342351370,
    489345219846733824,
]
LTLVC_EVENT_VOICE_CHANNEL_ID = 845603142368231424
LTLVC_EVENT_LOGGING_CHANNEL_ID = 845996258296725524

# LTLVC_EVENT_LOGGING_CHANNEL_ID = 836235473621352508
# LTLVC_EVENT_VOICE_CHANNEL_ID = 838387375591653377
class LastToLeaveVcError(commands.CommandError):
    pass


class LastToLeaveVc(BetterCog):
    def __init__(self, bot: PeaceBot):
        self.bot = bot
        super().__init__(bot)

        # Last to leave VC vars
        self.ltlvc_started = False
        self.ltlvc_main_started = False
        self.voice_client = None
        self.ltlvc_bot_kicked_users = []
        self.ltlvc_members_msg_cache = {}

    def cog_check(self, ctx: commands.Context):
        if ctx.guild.id == PRABHIDHIKAAR_GUILD_ID:
            return True
        return False

    def cog_help_check(self, ctx: commands.Context):
        if ctx.guild.id == PRABHIDHIKAAR_GUILD_ID:
            return True
        return False

    @tasks.loop(minutes=random.randrange(15, 25))
    async def message_check(self):
        if not self.ltlvc_main_started:
            return

        guild = self.bot.get_guild(PRABHIDHIKAAR_GUILD_ID)
        ltlvc_praticipants: List[discord.Member] = [
            member
            for member in (
                discord.utils.get(guild.roles, name="LtlVC Participants")
            ).members
            if not member.bot and member.id not in LTLVC_EVENT_MANAGERS
        ]
        for member in ltlvc_praticipants:
            asyncio.create_task(self.dm_random_check(member))

    async def dm_random_check(self, member: discord.Member):
        random_words = [
            "banana",
            "nettles",
            "apple",
            "bibhas",
            "uwu",
            "heheboi",
            "sus",
            "nou",
            "pegyan",
            "ahosha",
            "sussy",
        ]
        word = random.choice(random_words)
        await member.send(
            f"Reply with `{word}` within the next 120 seconds or get kicked!"
        )

        logging_channel = discord.utils.get(
            member.guild.text_channels, id=LTLVC_EVENT_LOGGING_CHANNEL_ID
        )

        try:
            def msg_check(m):
                return m.content.lower() == word

            await self.bot.wait_for(
                "message", check=msg_check, timeout=120
            )
            await member.send("You passed the AFK check!")
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title=f"Member Kicked From The Event!",
                description=f"{member.mention} was kicked from the ltlvc event, as the member didn't reply to dms!",
                color=discord.Color.red(),
            )
            self.ltlvc_bot_kicked_users.append(member)
            await member.move_to(
                channel=None,
                reason="Member didn't respond in time for the LTLVC dm check!",
            )
            await logging_channel.send(embed=embed)

    def ltlvc_start_check(
        self,
        member: discord.Member,
        old_state: discord.VoiceState,
        new_state: discord.VoiceState,
    ):
        return (
            member.guild.id == PRABHIDHIKAAR_GUILD_ID
            and (
                getattr(new_state.channel, "id", None) == LTLVC_EVENT_VOICE_CHANNEL_ID
                or getattr(old_state.channel, "id", None)
                == LTLVC_EVENT_VOICE_CHANNEL_ID
            )
            and self.ltlvc_started
        )

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        old_state: discord.VoiceState,
        new_state: discord.VoiceState,
    ):
        logging_channel = discord.utils.get(
            member.guild.text_channels, id=LTLVC_EVENT_LOGGING_CHANNEL_ID
        )
        voice_channel = discord.utils.get(
            member.guild.voice_channels, id=LTLVC_EVENT_VOICE_CHANNEL_ID
        )

        if not self.ltlvc_start_check(member, old_state, new_state):
            return

        if new_state.channel == voice_channel:
            embed = discord.Embed(
                title=f"Member Joined The Event!",
                description=f"{member.mention} joined the last to leave vc event!",
                color=discord.Color.green(),
            )
            await logging_channel.send(embed=embed)
        elif (
            old_state.channel == voice_channel
            and new_state.channel != voice_channel
            and member not in self.ltlvc_bot_kicked_users
        ):
            embed = discord.Embed(
                title=f"Member Left The Event!",
                description=f"{member.mention} left the last to leave vc event!",
                color=discord.Color.red(),
            )
            await logging_channel.send(embed=embed)

        voice_state_channel = new_state.channel or old_state.channel

        vc_members = [
            member
            for member in voice_state_channel.members
            if not member.bot and member.id not in LTLVC_EVENT_MANAGERS
        ]

        if len(vc_members) == 1 and self.ltlvc_main_started:
            embed = discord.Embed(
                title="Event has ended!",
                description="Last to leave VC event has ended!",
                color=discord.Color.gold(),
            )
            embed.add_field(name="Winner", value=vc_members[0].mention, inline=False)
            embed.add_field(
                name="Now What?", value="DM anyone mod/owner for claiming your prize ❤️"
            )
            await logging_channel.send(embed=embed)

            embed1 = discord.Embed(
                title="Bot Kicked Users!",
                description=", ".join(
                    [member.mention for member in self.ltlvc_bot_kicked_users]
                ),
                color=discord.Color.red(),
            )
            await logging_channel.send(embed=embed1)

            # End the event (Cleanup)!
            await self.cleanup()

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def ltlvc(self, ctx: commands.Context):
        await ctx.send_help(ctx.command)

    @ltlvc.command(name="start")
    async def ltlvc_start(self, ctx: commands.Context, wait_time: str):
        if self.ltlvc_started:
            raise LastToLeaveVcError("Event has already been started!")

        logging_channel: discord.TextChannel = discord.utils.get(
            ctx.guild.text_channels, id=LTLVC_EVENT_LOGGING_CHANNEL_ID
        )
        voice_channel: discord.VoiceChannel = discord.utils.get(
            ctx.guild.voice_channels, id=LTLVC_EVENT_VOICE_CHANNEL_ID
        )
        wait_time_sec = self.str_to_time(wait_time)

        overwrites = voice_channel.overwrites
        overwrites[ctx.guild.default_role] = PermissionOverwrite(connect=True)
        await voice_channel.edit(overwrites=overwrites)

        embed = discord.Embed(
            title="Event Started!",
            description="Last To Leave VC Event has been **STARTED**!",
            color=discord.Color.gold(),
            timestamp=ctx.message.created_at,
        )
        embed.add_field(
            name="Wait Time", value=f"{wait_time} from this message!", inline=False
        )
        embed.add_field(name="Voice Channel", value=voice_channel.mention)
        await ctx.send(f"**Event Started!**")
        await logging_channel.send(embed=embed)

        self.voice_client = await voice_channel.connect(reconnect=True)
        self.ltlvc_started = True
        await asyncio.sleep(wait_time_sec)

        vc_members = [
            member
            for member in voice_channel.members
            if not member.bot and member.id not in LTLVC_EVENT_MANAGERS
        ]

        if not vc_members:
            self.ltlvc_started = False
            await self.voice_client.disconnect()
            raise LastToLeaveVcError(
                "As there were no participants, the event has been cancelled!"
            )

        overwrites = voice_channel.overwrites
        overwrites[ctx.guild.default_role] = PermissionOverwrite(connect=False)
        self.ltlvc_main_started = True

        embed1 = discord.Embed(
            title="Main Event Started!",
            description="Voice Channel has been locked, and the main event has begun!",
            color=discord.Color.gold(),
            timestamp=ctx.message.created_at,
        )
        embed1.add_field(name="Participants", value=len(vc_members))

        self.message_check.start()
        await voice_channel.edit(overwrites=overwrites)
        await logging_channel.send(embed=embed1)

    @ltlvc.command(name="stop")
    async def ltlvc_stop(self, ctx: commands.Context):
        if not self.ltlvc_started:
            raise LastToLeaveVcError("Event has not been started!")

        logging_channel: discord.TextChannel = discord.utils.get(
            ctx.guild.text_channels, id=LTLVC_EVENT_LOGGING_CHANNEL_ID
        )
        voice_channel: discord.VoiceChannel = discord.utils.get(
            ctx.guild.voice_channels, id=LTLVC_EVENT_VOICE_CHANNEL_ID
        )

        embed = discord.Embed(
            title="Event Stopped!",
            description="Last To Leave VC Event has been **STOPPED**!",
            color=discord.Color.red(),
            timestamp=ctx.message.created_at,
        )

        overwrites = voice_channel.overwrites
        overwrites[ctx.guild.default_role] = PermissionOverwrite(connect=False)

        await ctx.send(f"**Event Stopped!**")
        await logging_channel.send(embed=embed)
        await voice_channel.edit(overwrites=overwrites)
        await self.cleanup()

    def str_to_time(self, time_str: str):
        time_regex = re.compile(r"(?:(\d{1,5})(h|s|m|d))+?")
        time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}

        args = time_str.lower()
        matches = re.findall(time_regex, args)
        time = 0
        for key, value in matches:
            try:
                time += time_dict[value] * float(key)
            except KeyError:
                raise commands.BadArgument(
                    f"{value} is an invalid time key! h|m|s|d are valid arguments"
                )
            except ValueError:
                raise commands.BadArgument(f"{key} is not a number!")
        return round(time)

    async def cleanup(self):
        self.ltlvc_started = False
        self.ltlvc_main_started = False
        await self.voice_client.disconnect()
        self.voice_client = None


def setup(bot):
    bot.add_cog(LastToLeaveVc(bot))
