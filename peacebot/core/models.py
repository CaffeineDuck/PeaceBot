"""This module contains the models for postgresql database"""

from tortoise import Model, fields

from ..env import peacebot_config


class GuildModel(Model):
    """
    `GuildModel` is used to store data about a guild in the database
    """

    id = fields.BigIntField(pk=True, description="Guild ID")
    prefix = fields.TextField(
        max_length=10,
        default=peacebot_config.prefix,
        description="Custom prefix of the guild",
    )

    # pylint: disable=R0903
    class Meta:
        """
        `GuildMode.Meta` is a meta class containg `GuildModel`'s
        database table info and description
        """

        table = "guilds"
        description = "Represent a discord guild's settings for PeaceBot"
