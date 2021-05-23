from typing import Optional

import discord
from discord.ext import commands

from bot.utils.mixins.better_cog import BetterCog

from bot.bot import PeaceBot
from bot.utils.events.last_to_leave_vc import LastToLeaveVc
from bot.utils.errors import NotPersonalGuild

PRABHIDHIKAAR_GUILD_ID = 836230453622341663

class Prabhidhikaar(BetterCog):
    def cog_check(self, ctx: commands.Context):
        if ctx.guild.id == PRABHIDHIKAAR_GUILD_ID:
            return True
        return False

    def cog_help_check(self, ctx: commands.Context):
        if ctx.guild.id == PRABHIDHIKAAR_GUILD_ID:
            return True
        return False

    @commands.group(name='loadevent', invoke_without_command=True)
    async def load_event(self, ctx: commands.Context):
        await ctx.send_help(ctx.command)
    
    @load_event.command(name='ltlvc')
    async def load_last_to_leave_vc(self, ctx: commands.Context):
        self.bot.add_cog(LastToLeaveVc(self.bot))
        await ctx.send('Last to leave vc has been loaded!')
    
    @commands.group(name='unloadevent', invoke_without_command=True)
    async def unload_event(self, ctx: commands.Context):
        await ctx.send_help(ctx.command)

    @unload_event.command(name='ltlvc')
    async def unload_last_to_leave_vc(self, ctx: commands.Context):
        self.bot.remove_cog('LastToLeaveVc')

def setup(bot: PeaceBot):
    bot.add_cog(Prabhidhikaar(bot))
