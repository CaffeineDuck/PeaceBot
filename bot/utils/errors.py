from discord.ext import commands


class CommandDisabled(commands.CheckFailure):
    def __init__(self, command: str, cog: str):
        self.command = command
        self.cog = cog

    def __str__(self):
        return f"The command `{self.command}` or its command group `{self.cog}` has been disabled in this channel!"


class NotPersonalGuild(commands.CommandError):
    def __str__(self):
        return "This command can only be used in my personal guild!"
