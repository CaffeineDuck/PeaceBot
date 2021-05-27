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
    users = fields.ManyToManyField("main.UserModel", related_name="Guild")
    image_banner = fields.TextField(
        description="BackGround image banner for the `rank` command", null=True
    )
    xp_multiplier = fields.IntField(description="Xp Multipication Value", default=1)
    xp_role_rewards = fields.JSONField(
        description="Role Rewards Level -> Role Mapping", null=True
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
    id = fields.UUIDField(pk=True)
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
    created_by = fields.ForeignKeyField(
        "main.UserModel", related_name="Autoresponses", null=True
    )

    class Meta:
        table = "autoresponses"
        table_description = "Represents the autoresponses for each GuildModel"


class CommandModel(Model):
    id = fields.UUIDField(pk=True)
    name = fields.TextField(description="Name of the cog or command!")
    enabled = fields.BooleanField(
        default=True, description="If the command/cog is enabled/disabled"
    )
    is_cog = fields.BooleanField(
        default=False, description="If the command/cog is a command"
    )
    guild = fields.ForeignKeyField("main.GuildModel", related_name="Commands")
    channel = fields.BigIntField(description="Channel of that disabled/enable command")

    class Meta:
        table = "commands"
        table_description = (
            "Represets all the enabled and disabled commands for each Guild"
        )


class LevelingUserModel(Model):
    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField("main.UserModel", related_name="LevelingUser")
    guild = fields.ForeignKeyField("main.GuildModel", related_name="LevelingUser")
    xp = fields.BigIntField(
        description="XP of the user in that guild!", default=0, null=True
    )
    level = fields.IntField(description="Level of the user!", default=0, null=True)
    image_banner = fields.TextField(
        description="BackGround image banner for the `rank` command", null=True
    )
    messages = fields.IntField(description='No. of messages sent by the user!', default=0)

    class Meta:
        table = "UserLeveling"
        table_description = "Represents the Leveling data for each user in a guild!"
