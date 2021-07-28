from ipaddress import IPv4Address
from pathlib import Path
from typing import Optional, Sequence

from pydantic import BaseModel, HttpUrl

from peacebot.core.types import VoiceRegions


class LavalinkConfig(BaseModel):
    host: IPv4Address
    port: int
    rest_url: HttpUrl
    idetifier: str
    region: VoiceRegions


class BotConfig(BaseModel):
    prefix: str
    description = 'A simple and shitty discord bot'
    cogs: Optional[Sequence[str]]
    cogs_dir: Optional[Path]
    lavalink_config: Optional[LavalinkConfig]
    db_config: Optional[dict]
    private_bot: Optional[bool] = False
    load_jishaku: Optional[bool] = True
