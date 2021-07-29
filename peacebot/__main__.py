"""
This is the main file for running the peacebot module using
`python -m peacebot`
"""
import os

from .core import PeaceBot
from .core.helpers import BotConfig
from .core.tortoise_config import tortoise_config
from .env import peacebot_config, peacebot_db_config, peacebot_lavalink_config

os.environ.setdefault("JISHAKU_HIDE", "1")
os.environ.setdefault("JISHAKU_RETAIN", "1")
os.environ.setdefault("JISHAKU_NO_UNDERSCORE", "1")


bot_config = BotConfig(
    prefix=peacebot_config.prefix,
    lavalink_config=peacebot_lavalink_config,
    # db_config=peacebot_db_config,
    token=peacebot_config.token,
)

bot = PeaceBot(config=bot_config, tortoise_config=tortoise_config)

if __name__ == "__main__":
    bot.run(bot_config.token)
