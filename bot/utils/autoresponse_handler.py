import discord
from discord.ext import commands


class AutoResponseError(commands.CommandError):
    pass


async def autoresponse_message_formatter(
    self, message: discord.Message, response: str
) -> str:
    """Formats the string to a valid message

    Args:
        message (str): Message object to format the string
        response (str): String to format using `message (str)`

    Returns:
        str: Converted string

    Raises:
        KeyError, AttributeError, AutoResponseError
    """
    try:
        # Checks if the mentions is needed in response
        mentioned = message.mentions[0] if "{mentioned}" in response else None
    except IndexError:
        raise AutoResponseError("You need to mention someone for this to work!")

    message_content = (
        " ".join(message.content.split(" ")[1:]) if "{message}" in response else None
    )

    if message_content == "":
        raise AutoResponseError(
            "You need to write some extra message for this to work!"
        )

    try:
        updated_message = response.format(
            author=message.author,
            message=message_content,
            raw_message=message,
            server=message.guild,
            mentioned=mentioned.mention,
        )
    except KeyError as error:
        raise AutoResponseError(
            f"""{str(error).replace("'", "`")} is not a valid arguement!"""
        )
    return updated_message
