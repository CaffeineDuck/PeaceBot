from ipaddress import IPv4Address
from pathlib import Path
from typing import Literal, Optional, Sequence, Union

from pydantic import BaseModel, HttpUrl

from .types import VoiceRegions


class DatabaseConfig(BaseModel):
    db: str
    host: Union[IPv4Address, Literal["localhost"]]
    password: str
    port: int = 5432
    user: str


class LavalinkConfig(BaseModel):
    host: Union[IPv4Address, Literal["localhost"]]
    port: int
    rest_url: str
    idetifier: str = "MAIN"
    region: VoiceRegions = VoiceRegions.INDIA


class BotConfig(BaseModel):
    prefix: str
    token: str
    cogs: Optional[Sequence[str]]
    cogs_dir: Optional[Path]
    lavalink_config: Optional[LavalinkConfig]
    db_config: Optional[DatabaseConfig]
    private_bot = False
    description = "A simple and shitty discord bot"
    load_jishaku = True
