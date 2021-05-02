from discord.ext.commands import CheckFailure


class CommandDisabled(CheckFailure):
    def __init__(self, command: str, cog: str):
        self.command = command
        self.cog = cog

    def __str__(self):
        return f"The command `{self.command}` or its command group `{self.cog}` has been disabled in this channel!"
