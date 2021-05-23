"""
Author of the following code:
https://github.com/falsedev
"""

import asyncio
import inspect
import re
from datetime import datetime
from enum import Enum
from typing import Callable, List, Mapping, Optional, Type, Union

from discord import Color, Embed, Member, Message, Reaction, User
from discord.abc import Messageable
from discord.ext import commands

from bot.utils.mixins.better_cog import BetterCog

from .convert import UserInputable, convert_to_type, to_str


class Prompt:
    """A class representing a prompt in the embed wizard"""

    def __init__(
        self,
        key: str,
        description: str,
        title: Optional[str] = None,
        out_type: Type[type] = str,
        check: Optional[Callable] = None,
        post_check: Optional[Callable] = None,
        timeout: int = 120,
        reaction_interface: bool = False,
    ):
        self.key = key
        self.title: str = title or key.capitalize()
        self.description = description
        self.type = out_type
        self.check = check
        self.post_check = post_check
        self.timeout = timeout
        self.reaction_interface = reaction_interface


class Wizard:
    def __init__(
        self,
        bot: commands.Bot,
        commander: Member,
        prompts: List[Prompt],
        title: str,
        embed_color=0xF1C40F,
        completed_message: str = "Wizard Complete",
        return_dict: bool = False,
        confirm_prompt: bool = False,
    ):
        self.total_steps = len(prompts)
        self.embed = Embed(
            title=title,
            description=f"Step 1 of {len(prompts)}",
            color=embed_color,
            timestamp=datetime.utcnow(),
        )
        self.waiting = "Waiting for your input..."
        self.message = None
        self.__prompts = prompts
        self.bot = bot
        self.commander = commander
        self.completed_message = completed_message
        self.__step = 0

        # Flags
        self.return_dict = return_dict
        self.confirm_prompt = confirm_prompt

    @property
    def step(self):
        return self.__step

    @step.setter
    def step(self, new: int):
        self.__step = new
        # __step is supposed to be the array index used for prompts
        self.embed.description = f"Step {new + 1} of {self.total_steps}"

    @property
    def prompts(self) -> List[Prompt]:
        return self.__prompts

    @prompts.setter
    def prompts(self, new: List[Prompt]):
        self.__prompts = new
        self.total_steps = len(new)
        self.step = self.step

    def default_check(self, message: Message) -> bool:
        return all(
            (message.author == self.commander, message.channel == self.message.channel)
        )

    async def start(self, location: Messageable) -> None:
        """Sends the initial wizard
        Parameters
        ----------
        location : discord.abc.Messageable
            The place to send the embed to
        Raises
        ------
        RuntimeError
            If the message has already been sent once before
        """
        if self.message is not None:
            raise RuntimeError("Message already sent")

        self.embed.add_field(
            name=self.prompts[self.step].title, value=self.waiting, inline=False
        )
        self.embed.add_field(
            name="Description", value=self.prompts[self.step].description, inline=False
        )
        self.message = await location.send(embed=self.embed)

    def default_reaction_check(self, r: Reaction, u: User) -> bool:
        return all((u == self.commander, r.message == self.message))

    def enum_default_check(self, r: Reaction, u: User) -> bool:
        return all((self.default_reaction_check(r, u), not r.custom_emoji))

    async def get_bool_rr_input(self, prompt):
        await self.message.clear_reactions()
        await self.message.add_reaction("\u2705")
        await self.message.add_reaction("\u274E")
        checks = self._combine_checks(self.default_reaction_check, prompt.check)

        def bool_check(r, u):
            return checks(r, u) and r.emoji in ("\u2705", "\u274E")

        r, _ = await self.bot.wait_for(
            "reaction_add", check=bool_check, timeout=prompt.timeout
        )
        await self.message.clear_reactions()
        return r.emoji == "\u2705"

    async def get_enum_rr_input(self, prompt: Prompt):
        opt_len = len(prompt.type)
        await self.message.clear_reactions()
        for i in range(opt_len):
            await self.message.add_reaction(chr(i + 127462))

        checks = self._combine_checks(self.enum_default_check, prompt.check)

        def enum_check(r, u):
            return checks(r, u) and 127462 + opt_len > ord(r.emoji) > 127461

        reaction, _ = await self.bot.wait_for(
            "reaction_add", check=enum_check, timeout=prompt.timeout
        )
        result = list(prompt.type)[ord(reaction.emoji) - 127462]
        await self.message.clear_reactions()
        return result

    async def get_enum_input(self, prompt: Prompt):
        opt_len = len(prompt.type)
        checks = self._combine_checks(self.default_check, prompt.check)

        def enum_check(m):
            return (
                checks(m)
                and len(m.content) == 1
                and (
                    ord(m.content) in range(65, 65 + opt_len)
                    or ord(m.content) in range(97, 97 + opt_len)
                )
            )

        msg = await self.bot.wait_for(
            "message", check=enum_check, timeout=prompt.timeout
        )
        return list(prompt.type)[ord(msg.content) - (msg.content.islower() * 32) - 65]

    def _combine_checks(self, default_check, custom_check):
        return lambda *args: default_check(*args) and (
            custom_check(*args) if custom_check else True
        )

    async def _get_input(self, prompt):
        if issubclass(prompt.type, Enum):
            if prompt.reaction_interface:
                return await self.get_enum_rr_input(prompt)
            return await self.get_enum_input(prompt)

        if prompt.type is Reaction:
            result, _ = await self.bot.wait_for(
                "reaction_add",
                check=self._combine_checks(self.default_reaction_check, prompt.check),
                timeout=prompt.timeout,
            )
            await self.message.clear_reactions()
            return result

        if prompt.type is bool and prompt.reaction_interface:
            return await self.get_bool_rr_input(prompt)

        while True:
            response = await self.bot.wait_for(
                "message",
                check=self._combine_checks(self.default_check, prompt.check),
                timeout=prompt.timeout,
            )
            await response.delete()
            ctx = await self.bot.get_context(self.message)
            try:
                result = await convert_to_type(ctx, prompt.type, response.content)
            except commands.CommandError as error:
                await self.on_invalid_input(error)
            else:
                break
        return result

    async def step_forward(self) -> UserInputable:
        """Runs one step of the wizard
        Parameters
        ----------
        check : Optional[Callable], optional
            The check to call along with the default one
            which will check for the same author and channel, by default None
        Returns
        -------
        UserInputable
            The content of the response
        """
        prompt = self.prompts[self.step]

        while True:
            result = await self._get_input(prompt)
            if prompt.post_check is None:
                break  # Leave loop if no post check
            if inspect.iscoroutinefunction(prompt.post_check):
                # post check is a coroutine
                error_message = await prompt.post_check(result)
            else:
                # post check is a regular function
                error_message = prompt.post_check(result)
            if not error_message:
                break  # Leave loop is no error message
            await self.on_invalid_input(commands.CommandError(error_message))

        self.embed.set_field_at(
            self.step, name=prompt.title, value=to_str(result), inline=False
        )
        if prompt.type is str and len(result) > 1024:
            # Max length check for embed field
            self.embed.set_field_at(
                self.step,
                name=prompt.title,
                value="```Content exceeds embed's limit!```",
                inline=False,
            )

        if self.step + 1 < len(self.prompts):
            next_prompt = self.prompts[self.step + 1]
            self.step += 1
            self.embed.set_field_at(
                -1, name="Description", value=next_prompt.description, inline=False
            )
            self.embed.insert_field_at(
                -1, name=next_prompt.title, value=self.waiting, inline=False
            )

        await self.update_message()

        return result

    async def on_invalid_input(self, error: commands.CommandError):
        return await self.message.channel.send(
            embed=Embed(
                title="Invalid input, try again",
                description=f"The input you provided was invalid\n{error}",
                color=Color.red(),
            ),
            delete_after=10,
        )

    async def finish_wizard(self):
        self.embed.remove_field(-1)
        self.embed.description = self.completed_message
        self.embed.color = Color.green()

    async def update_message(self):
        return await self.message.edit(embed=self.embed)

    async def confirm_inputs(self):
        self.embed.set_field_at(
            -1,
            name="Confirm",
            value="Reply 0 to confirm these or input number to edit that input",
            inline=False,
        )
        await self.update_message()
        while True:
            try:
                while True:
                    field_no = await self._get_input(Prompt("", "", "", int, ())) - 1
                    if len(self.prompts) >= field_no >= -1:
                        break
                    else:
                        await self.on_invalid_input(
                            commands.CommandError("Invalid input")
                        )
            except asyncio.TimeoutError:
                break

            if field_no == -1:
                break

            prompt = self.prompts[field_no]
            result = await self._get_input(prompt)
            self.results[field_no] = result
            self.embed.set_field_at(field_no, name=prompt.title, value=to_str(result))
            # self.embed.remove_field(-2)
            await self.update_message()

    async def run(
        self, location: Messageable
    ) -> Union[List[UserInputable], Mapping[str, UserInputable]]:
        """Runs the wizard all the way through,
        use this if you don't wish to use any custom
        checks in any step
        Parameters
        ----------
        location : discord.abc.Messageable
            The channel to send the wizard to
        Returns
        -------
        Union[ List[UserInputable], Mapping[str, UserInputable] ]
            All the responses given
        """
        await self.start(location)
        self.results = [await self.step_forward() for prompt in self.prompts]
        if self.confirm_prompt:
            await self.confirm_inputs()
        await self.finish_wizard()
        await self.update_message()
        if self.return_dict:
            return {
                self.prompts[i].key: self.results[i] for i in range(len(self.prompts))
            }
        return self.results
