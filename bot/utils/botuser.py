import discord
from discord.ext import commands


class BotUser(commands.Converter):
    async def convert(self, ctx: commands.Context, argument):
        if not argument.isdigit():
            raise commands.BadArgument("Not a valid bot user ID.")
        try:
            user = await ctx.bot.fetch_user(argument)
            if user in ctx.guild.members:
                raise commands.BadArgument("This bot is already in this guild!")

        except discord.NotFound:
            raise commands.BadArgument("Bot user not found (404).")
        except discord.HTTPException as e:
            raise commands.BadArgument(f"Error fetching bot user: {e}")
        else:
            if not user.bot:
                raise commands.BadArgument("This is not a bot.")
            return user
