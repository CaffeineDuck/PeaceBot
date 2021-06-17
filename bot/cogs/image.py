from bot.utils.mixins.better_cog import BetterCog
from typing import Optional
import inspect

from discord.ext.commands import CogMeta, Command, BucketType, cooldown
from discord.ext.commands import Context
from discord import Member, File

from bot.utils.imggen.imggen.core import BaseImageGenerator, ImageType
from bot.utils.imggen.imggen.meme import MemeGenerator


def image_paste_command(func_name: str):
    async def image_paste(self, ctx: Context, *, member: Optional[Member] = None):
        f"Generates a {func_name} image with given user's avatar"
        user = member or ctx.author
        av = await user.avatar_url_as(size=128).read()
        b = await getattr(self.generator, func_name)(av)
        await ctx.send(file=File(b, filename="image.jpg"))

    return image_paste


def text_write_command(func_name: str, param_count: int = 1):
    if param_count == 1:

        async def image_text_one_arg(self, ctx: Context, *, text: str):
            f"Generates a {func_name} image with given text"
            b = await getattr(self.generator, func_name)(text)
            await ctx.send(file=File(b, filename="image.jpg"))

        return image_text_one_arg

    async def image_text(self, ctx: Context, *texts: str):
        f"Generates a {func_name} image with given text"
        if len(texts) != param_count:
            return await ctx.send(f"I need {param_count} arguments, got {len(texts)}")

        b = await getattr(self.generator, func_name)(*texts)
        await ctx.send(file=File(b, filename="image.jpg"))

    return image_text


class ImageGenCogMeta(CogMeta):
    def __new__(cls, name, bases, attrs, *, generator: BaseImageGenerator, **kwargs):
        for attr_name in dir(generator):
            attr = getattr(generator, attr_name)
            if not getattr(attr, "__image_generator__", False):
                continue
            signature = inspect.signature(attr)
            params = signature.parameters
            if len(params) == 2 and list(params.values())[1].annotation == ImageType:
                cmd = Command(image_paste_command(attr_name), name=attr_name)

            elif all([p.annotation == str for p in list(params.values())[1:]]):
                cmd = Command(
                    text_write_command(attr_name, len(params) - 1), name=attr_name
                )

            else:
                raise RuntimeError("Unknown image generator args")

            cooldown(1, 5, BucketType.user)(cmd)
            attrs[attr.__name__] = cmd
        self = super().__new__(cls, name, bases, attrs, **kwargs)
        return self


class Image(BetterCog, metaclass=ImageGenCogMeta, generator=MemeGenerator):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot
        self.generator = MemeGenerator(async_mode=True)


def setup(bot):
    bot.add_cog(Image(bot))
