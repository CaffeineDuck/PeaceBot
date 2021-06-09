from typing import Optional

from discord.ext import commands

from bot.bot import PeaceBot


class CommandCannotRun(commands.CommandError):
    def __init__(self, error_msg: Optional[str]):
        self.error_msg = error_msg or "This command can't run be here by this user!"

    def __str__(self):
        return self.error_msg


class BetterCog(commands.Cog):
    def __init__(
        self,
        bot: PeaceBot,
        error_msg: Optional[str] = None,
        cog_hidden: bool = False,
        *args,
        **kwargs
    ):
        self.bot = bot
        self.hidden = cog_hidden
        self.error_msg = error_msg
        super().__init__(*args, **kwargs)

    def help_check(self, ctx: commands.Context):
        if self.cog_help_check(ctx) == True:
            return True
        raise CommandCannotRun(self.error_msg)

    def cog_help_check(self, ctx: commands.Context):
        return True
