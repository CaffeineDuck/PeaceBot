"""This module contains all the config stuff for initializing `peacebot`"""

# pylint: disable=R0903

from ipaddress import IPv4Address
from pathlib import Path
from typing import Literal, Optional, Sequence, Union

# pylint: disable=E0611
from pydantic import BaseModel

from .types import VoiceRegions


class DatabaseConfig(BaseModel):
    """
    This is a model containing database info
    """

    db: str
    host: Union[IPv4Address, Literal["localhost"]]
    password: str
    port: int = 5432
    user: str


class LavalinkConfig(BaseModel):
    """
    This is a model containing lavalink info
    """

    host: Union[IPv4Address, Literal["localhost"]]
    port: int
    rest_url: str
    identifier: str = "MAIN"
    region: VoiceRegions = VoiceRegions.INDIA
    password: str


class BotConfig(BaseModel):
    """
    This is a model containg the bot config info
    """

    prefix: str
    token: str
    cogs: Optional[Sequence[str]]
    cogs_dir: Optional[Path]
    lavalink_config: Optional[LavalinkConfig]
    db_config: Optional[DatabaseConfig]
    private_bot = False
    description = "A simple and shitty discord bot"
    load_jishaku = True
