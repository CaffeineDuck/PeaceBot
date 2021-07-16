import os

from discord.ext import commands

from .bot import PeaceBot

os.environ.setdefault("JISHAKU_HIDE", "1")
os.environ.setdefault("JISHAKU_RETAIN", "1")
os.environ.setdefault("JISHAKU_NO_UNDERSCORE", "1")

if __name__ == "__main__":
    from config.bot import bot_config
    from tortoise_config import tortoise_config
    from config.misc import misc_settings

    bot = PeaceBot(
        tortoise_config=tortoise_config,
        prefix=bot_config.prefix,
        developement_environment=bot_config.developement_environment,
        log_webhook_url=misc_settings.log_webhook_url,
    )

    bot.run(bot_config.token)
