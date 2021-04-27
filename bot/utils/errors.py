from discord.ext.commands import CheckFailure


class CommandDisabled(CheckFailure):
    def __str__(self):
        return "This command has been disabled in this channel!"
