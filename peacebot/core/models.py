from tortoise import fields, Model
from ..env import peacebot_config

class GuildModel(Model):
    id = fields.BigIntField(pk=True, description='Guild ID')
    prefix = fields.TextField(max_length = 10, default=peacebot_config.prefix, description="Custom prefix of the guild")

    class Meta:
        table = "guilds"
        description = "Represent a discord guild's settings for PeaceBot"
