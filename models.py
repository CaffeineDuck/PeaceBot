from discord import Guild
from discord.ext.commands import Context
from tortoise import Model, fields

from config.bot import bot_config


class GuildModel(Model):
    id = fields.BigIntField(pk=True, description="Discord ID of the guild")
    prefix = fields.CharField(
        max_length=10,
        default=bot_config.prefix,
        description="Custom prefix of the guild",
    )

    @classmethod
    async def from_id(cls, guild_id: int):
        return (await cls.get_or_create(id=guild_id))[0]

    @classmethod
    async def from_guild_object(cls, guild: Guild):
        return await cls.from_id(guild.id)

    @classmethod
    async def from_context(cls, ctx: Context):
        return await cls.from_id(ctx.guild.id)

    class Meta:
        table = "guilds"
        table_description = "Represents a discord guild's settings"


class UserModel(Model):
    id = fields.BigIntField(pk=True, description="Discord ID of the user")

    class Meta:
        table = "users"
        table_description = "Represents all users"


class AutoResponseModel(Model):
    id = fields.IntField(pk=True)
    trigger = fields.TextField(description="Trigger for the autoresponse")
    response = fields.TextField(
        default=None,
        null=True,
        description="Response to be sent after being triggered from the trigger",
    )
    enabled = fields.BooleanField(
        default=False, description="Boolean to show of the trigger is enabled"
    )
    extra_arguements = fields.BooleanField(
        default=False,
        description="If the autoresponse should be run even when extra arguements are passed",
    )
    has_variables = fields.BooleanField(
        default=False, description="If the autoresponse output has variables"
    )
    guild = fields.ForeignKeyField("main.GuildModel", related_name="Autoresponses")

    class Meta:
        table = "autoresponses"
        table_description = "Represents the autoresponses for each GuildModel"
