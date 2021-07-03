import contextlib
import re
import traceback

import discord
from discord import Color, Embed
from discord.ext import commands

from bot.utils.error_logging import error_to_embed
from bot.utils.mixins.better_cog import BetterCog


class ErrorHandler(BetterCog):
    @commands.Cog.listener()
    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        embeds = error_to_embed()
        context_embed = Embed(
            title="Context", description=f"**Event**: {event_method}", color=Color.red()
        )
        await self.bot.log_webhook.send(embeds=[*embeds, context_embed])

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.CommandNotFound):
            return

        if not isinstance(error, commands.CommandInvokeError):
            if isinstance(error, commands.BotMissingPermissions):
                return await ctx.reply(
                    f"I am missing the following permissions:\n **{','.join(error.missing_perms)}**"
                )
            elif isinstance(error, commands.MissingPermissions):
                return await ctx.reply(
                    f"You are missing the following permissions:\n**{','.join(error.missing_perms)}**"
                )
            elif isinstance(error, commands.NSFWChannelRequired):
                image = "https://i.imgur.com/oe4iK5i.gif"
                embed = discord.Embed(
                    title="NSFW not allowed here",
                    description="Use NSFW commands in a NSFW marked channel.",
                    color=discord.Color.dark_blue(),
                )
                embed.set_image(url=image)
                return await ctx.reply(embed=embed)
            else:
                title = " ".join(
                    re.compile(r"[A-Z][a-z]*").findall(error.__class__.__name__)
                )
                return await ctx.send(
                    embed=Embed(title=title, description=str(error), color=Color.red())
                )

        # If we've reached here, the error wasn't expected
        # Report to logs
        if self.bot.developement_environment:
            return traceback.print_exception(type(error), error, error.__traceback__)

        embed = Embed(
            title="Error",
            description="An unknown error has occurred and my developer has been notified of it.",
            color=Color.red(),
        )
        with contextlib.suppress(discord.NotFound, discord.Forbidden):
            await ctx.send(embed=embed)

        traceback_embeds = error_to_embed(error)

        # Add message content
        info_embed = Embed(
            title="Message content",
            description="```\n"
            + discord.utils.escape_markdown(ctx.message.content)
            + "\n```",
            color=Color.red(),
        )
        # Guild information
        value = (
            (
                "**Name**: {0.name}\n"
                "**ID**: {0.id}\n"
                "**Created**: {0.created_at}\n"
                "**Joined**: {0.me.joined_at}\n"
                "**Member count**: {0.member_count}\n"
                "**Permission integer**: {0.me.guild_permissions.value}"
            ).format(ctx.guild)
            if ctx.guild
            else "None"
        )

        info_embed.add_field(name="Guild", value=value)
        # Channel information
        if isinstance(ctx.channel, discord.TextChannel):
            value = (
                "**Type**: TextChannel\n"
                "**Name**: {0.name}\n"
                "**ID**: {0.id}\n"
                "**Created**: {0.created_at}\n"
                "**Permission integer**: {1}\n"
            ).format(ctx.channel, ctx.channel.permissions_for(ctx.guild.me).value)
        else:
            value = (
                "**Type**: DM\n" "**ID**: {0.id}\n" "**Created**: {0.created_at}\n"
            ).format(ctx.channel)

        info_embed.add_field(name="Channel", value=value)

        # User info
        value = (
            "**Name**: {0}\n" "**ID**: {0.id}\n" "**Created**: {0.created_at}\n"
        ).format(ctx.author)

        info_embed.add_field(name="User", value=value)

        await self.bot.log_webhook.send(
            content="---------------\n\n**NEW ERROR**\n\n---------------",
            embeds=[*traceback_embeds, info_embed],
        )


def setup(bot: commands.Bot):
    bot.add_cog(ErrorHandler(bot))
