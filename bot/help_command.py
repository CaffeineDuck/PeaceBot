from typing import Mapping, Optional, List

from discord import Embed, Color
from discord.ext import commands


class HelpCommand(commands.HelpCommand):
    def command_not_found(self, string: str) -> str:
        return f"I don't have the command `{string}`, if you have an idea for this use `suggest` command!"

    def subcommand_not_found(self, command: commands.Command, string: str) -> str:
        return f"I don't have the command `{command.qualified_name} {string}`, if you have an idea for this use `suggest` command!"

    async def dispatch_help(self, help_embed: Embed) -> None:
        dest = self.get_destination()
        await dest.send(embed=help_embed)

    async def send_error_message(self, error: str) -> None:
        embed = Embed(title="Sorry :\\", description=error, color=Color.blue())
        await self.dispatch_help(embed)

    async def send_bot_help(
        self, mapping: Mapping[Optional[commands.Cog], List[commands.Command]]
    ) -> None:
        bot = self.context.bot
        embed = Embed(
            title=f"{bot.user.name} help",
            description=f"Here's everything I can do!",
            color=Color.blue(),
        )
        for cog in self.context.bot.cogs.values():
            # Removes Jishaku!
            if cog.qualified_name == "Jishaku":
                continue
            help_string = (
                cog.__doc__ if cog.__doc__ is not None else "No help available"
            )
            embed.add_field(
                name=cog.qualified_name,
                value=f"{help_string}\n`{self.clean_prefix}help {cog.qualified_name}`",
            )
        await self.dispatch_help(embed)

    async def send_command_help(self, command: commands.Command) -> None:
        embed = Embed(
            title=f"Help for command: `{command.name}`",
            description=f"Let me show you what the command {command.qualified_name} is all about!",
            color=Color.blue(),
        )
        embed.add_field(
            name="What does this command do?", value=command.help, inline=False
        )
        embed.add_field(
            name="Usage", value=f"`{self.get_command_signature(command)}`", inline=False
        )
        await self.dispatch_help(embed)

    async def send_group_help(self, group: commands.Group) -> None:
        embed = Embed(
            title=f"Help for command: `{group.name}`",
            description=f"Let me show you what the command {group.qualified_name} is all about!",
            color=Color.blue(),
        )
        embed.add_field(
            name="What does this command do?", value=group.help, inline=False
        )
        embed.add_field(
            name="Usage", value=f"`{self.get_command_signature(group)}`", inline=False
        )
        subcommand_help = [
            f"**`{self.get_command_signature(command)}`**\n{command.help}"
            for command in group.commands
        ]
        newline = "\n"
        embed.add_field(
            name="Related commands",
            value=f"\n{newline.join(subcommand_help)}",
            inline=False,
        )
        await self.dispatch_help(embed)

    async def send_cog_help(self, cog: commands.Cog) -> None:
        embed = Embed(
            title=f"Help for extension: `{cog.qualified_name}`",
            description="Ooooh ther's lots of fun stuff in here!",
            color=Color.blue(),
        )
        embed.add_field(
            name="What does this extension do?", value=cog.__doc__, inline=False
        )
        for command in cog.walk_commands():
            if command.parent is None:
                embed.add_field(
                    name=f"`{self.clean_prefix}{command.name}`", value=command.help
                )
        await self.dispatch_help(embed)
