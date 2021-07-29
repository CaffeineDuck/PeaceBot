"""This module contains BetterCog and other required methods for it"""
import logging
from typing import Optional, Union

import discord
from discord.ext import commands

from peacebot import PeaceBot


class CommandCannotRun(commands.CommandError):
    """This error is raised when a command can't be run"""

    def __str__(self):
        return "This command can't run be here by this user!"


class BetterCog(commands.Cog):
    """`BetterCog` is commands.Cog but better suited to `PeaceBot`"""

    def __init__(
        self,
        bot: PeaceBot,
        error_msg: Optional[str] = None,
        cog_hidden: Optional[bool] = False,
        **kwargs,
    ):
        self.bot = bot
        self.hidden = cog_hidden
        self.error_msg = error_msg
        super().__init__(**kwargs)

        self.logger = logging.getLogger(f"peacebot.cogs.{self.__class__.__name__}")

    def help_check(self, ctx: commands.Context) -> bool:
        """
        This method is called in HelpCommand to check
        if the cog/command can be shown in help command
        """
        if self.cog_help_check(ctx):
            return True
        raise CommandCannotRun(self.error_msg)

    # pylint: disable=W0613, R0201
    def cog_help_check(self, ctx: commands.Context) -> bool:
        """
        This method is called in `BetterCog.help_check` method
        used to determine if to show or not to show in help command
        """
        return True

    # pylint: disable=W0613, R0201
    def cog_is_disabled(self, channel_id: Optional[int] = None) -> bool:
        """
        This method is called to check if the instance's cog
        is disabled in the given channel
        """
        return False

    # pylint: disable=W0613, R0201
    async def delete_user_data(
        self,
        user: Union[discord.User, discord.Member],
        guild_only: Optional[bool] = True,
    ) -> bool:
        """
        This method is called from every cog whenever a
        delete user data method is called
        """
