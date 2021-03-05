from typing import Mapping, Optional, List

from discord import Embed, Color
from discord.ext import commands

INVISIBLE_COGS = ["ErrorHandler", "Jishaku", "PersonalGuild"]

NSFW_COGS = ["NSFW"]


class HelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(show_hidden=False, verify_checks=True)

    async def nsfw_cog_checker(self, cog: commands.Cog):
        if cog.qualified_name in NSFW_COGS:
            if self.context.channel.is_nsfw():
                return True
            return False
        return True

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

        embed.set_footer(
            text="Please keep in mind that these extensions are case sensitive!"
        )

        for cog in self.context.bot.cogs.values():
            if cog.qualified_name in INVISIBLE_COGS or not await self.nsfw_cog_checker(
                cog
            ):
                continue
            embed.add_field(
                name=cog.qualified_name,
                value=f"`{self.clean_prefix}help {cog.qualified_name}`",
            )
        await self.dispatch_help(embed)

    async def send_command_help(self, command: commands.Command) -> None:
        if not await command.can_run(self.context):
            raise self.command_not_found(command.name)
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
            if await command.can_run(self.context)
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
        command = commands.Command

        filtered_commands = await self.filter_commands(cog.walk_commands())

        commands_in_cog = [
            f"`{command.name}`"
            for command in filtered_commands
            if command.parent is None
        ]

        embed.add_field(
            name="Commands:",
            value=(", ".join(commands_in_cog))
            if commands_in_cog
            else "No Commands Found!",
        )
        await self.dispatch_help(embed)
