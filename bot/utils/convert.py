"""
Author of the following code:
https://github.com/falsedev
"""
from enum import Enum
from typing import Callable, List, Optional, Type, Union

from discord import (
    CategoryChannel,
    Color,
    Embed,
    Emoji,
    Invite,
    Member,
    Message,
    PartialEmoji,
    Reaction,
    Role,
    TextChannel,
    User,
    VoiceChannel,
)
from discord.ext import commands

from bot.utils.mixins.better_cog import BetterCog
from discord.utils import escape_markdown, escape_mentions

UserInputable = Union[
    str,
    int,
    Enum,
    User,
    Member,
    Role,
    CategoryChannel,
    TextChannel,
    VoiceChannel,
    Reaction,
    Emoji,
    PartialEmoji,
    Color,
    Invite,
]


def built_in_converter(target_type: Type[type]):
    def converter(argument: str):
        nonlocal target_type
        try:
            return target_type(argument)
        except Exception as exc:
            raise commands.CommandError(
                f'Conversion of "{argument}" to {target_type.__class__.__name__} failed: {exc}'
            )

    return converter


type_to_converter = {
    # Builtins
    bool: commands.core._convert_to_bool,
    int: built_in_converter(int),
    str: str,
    # Discord objects
    Role: commands.RoleConverter(),
    User: commands.UserConverter(),
    Member: commands.MemberConverter(),
    Color: commands.ColorConverter(),
    Invite: commands.InviteConverter(),
    Emoji: commands.EmojiConverter(),
    Message: commands.MessageConverter(),
    PartialEmoji: commands.PartialEmojiConverter(),
    TextChannel: commands.TextChannelConverter(),
    VoiceChannel: commands.VoiceChannelConverter(),
    CategoryChannel: commands.CategoryChannelConverter(),
}

_to_str = {
    Message: lambda m: f"Message with id {m.id} in {m.channel.mention}",
}


def to_str(argument: UserInputable) -> str:
    _type = type(argument)
    if issubclass(_type, Enum):
        return argument.name.capitalize().replace("_", " ")
    if _type is Reaction:
        if argument.custom_emoji:
            e = argument.emoji
            if isinstance(e, PartialEmoji):
                return e.name
            return f"<{'a'*e.animated}:{e.name}:{e.id}>"
        return argument
    if _type in _to_str:
        return _to_str[type(argument)](argument)
    if hasattr(argument, "mention"):
        return argument.mention
    return str(argument)


async def convert_to_type(
    ctx: commands.Context, type: Type[type], content: str, overrides={}
) -> UserInputable:
    converter = type_to_converter[type] if type not in overrides else overrides[type]
    if isinstance(converter, commands.Converter):
        return await converter.convert(ctx, content)
    return converter(content)
