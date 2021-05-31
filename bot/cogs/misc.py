import asyncio
from bot.bot import PeaceBot
import random
from typing import Union

import discord
from akinator.async_aki import Akinator
from discord import Color, Embed, Member, Message
from discord.ext import commands
from discord.ext.commands import BucketType, Context
from nepse import Client

from bot.utils.mixins.better_cog import BetterCog

HTTP_ERROR_VALID_RANGES = (
    (100, 102),
    (200, 208),
    (300, 308),
    (400, 452),
    (499, 512),
    (599, 600),
)

AKINATOR_RESPONSES = {
    "yes": ("yes", "y", "0"),
    "no": ("no", "n", "1"),
    "idk": ("idk", "i", "2"),
    "back": ("probably", "p", "3"),
    "probably": ("probably not", "pn", "4"),
    "stop": ("stop", "s", "5"),
    "back": ("back", "b", "6"),
}


class AkiError(commands.CommandError):
    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return self.message


class Misc(BetterCog):
    def __init__(self, bot: PeaceBot):
        super().__init__(bot)
        self._share_client = Client()

    @commands.command()
    async def nepse(self, ctx: commands.Context, symbol: str):
        symbol = symbol.upper()
        response = await self._share_client.get_company(symbol=symbol)
        daily_trade = response.security_daily_trade_dto
        
        embed = discord.Embed(
            title=f"NEPSE Data for {response.security.security_name}",
            color=discord.Color(random.randint(0, 0xFFFFFF)),
        )
        embed.set_thumbnail(
            url="https://images-ext-2.discordapp.net/external/ciTNJpWs61J0Ur_U5DQHFSpJ8DsvgPGjfbsedMtSkyc/https/images-ext-2.discordapp.net/external/rxvZr7oPFnT1PYp5DHluOA9a1F2d-wiUD-SgZ2LknZ8/https/cdn6.aptoide.com/imgs/a/8/4/a8435b6d8d3424dbc79a4ad52f976ad7_icon.png"
        )
        embed.add_field(name="Open Price", value=daily_trade.open_price, inline=False)
        embed.add_field(
            name="Highest Price", value=daily_trade.high_price, inline=False
        )
        embed.add_field(name="Lowest Price", value=daily_trade.low_price, inline=False)
        embed.add_field(
            name="Closing Price", value=daily_trade.close_price, inline=False
        )
        embed.add_field(
            name="Last Updated Price", value=daily_trade.last_traded_price, inline=False
        )

        embed.set_footer(text=f"Business Date: {daily_trade.business_date}")
        await ctx.reply(embed=embed)

    @commands.command(name="httpcat", aliases=["hcat"])
    async def httpcat(self, ctx, code: Union[int, str] = None):
        """Get a HTTP Cat for a HTTP error code"""

        title = None

        in_valid_range = any((code in range(*i) for i in HTTP_ERROR_VALID_RANGES))

        if code is None:
            code = 400
            title = "Ask with a code"

        elif isinstance(code, str):
            code = 422
            title = "Invalid number code"

        elif not in_valid_range:
            code = 404
            title = "Can't find that code..."

        url = f"https://http.cat/{code}"
        if not title:
            title = str(code)

        embed = Embed(title=title, color=Color(random.randint(0, 0xFFFFFF)))
        embed.set_image(url=url)
        await ctx.reply(embed=embed)

    @commands.command(name="akinator", aliases=["aki"])
    @commands.max_concurrency(1, per=commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.channel)
    async def aki(self, ctx: commands.Context):
        """Play akinator!
        **Always respond within 30 seconds**
        Valid question responses:
        - **Yes**: yes, y, 0
        - **No**: no, n, 1
        - **I don't know**: i, idk, 2
        - **Probably**: probably, p, 3
        - **Probably Not**: probably not, pn, 4
        - **Stop**: stop, s, 5
        - **Back**: back, b, 6
        """

        await ctx.trigger_typing()

        index = 1
        akinator = Akinator()
        question = await akinator.start_game(child_mode=True)

        # Convert the list of tupes of values into a list of all the valid responses
        akinator_valid_responses = [
            response for values in AKINATOR_RESPONSES.values() for response in values
        ]

        def check(message: Message):
            return (
                message.channel == ctx.channel
                and message.author == ctx.author
                and message.content.lower() in akinator_valid_responses
            )

        while akinator.progression <= 80:
            await ctx.trigger_typing()

            embed = Embed(
                title=f"{ctx.author.display_name}, Question {index}",
                color=Color.gold(),
                timestamp=ctx.message.created_at,
            )
            embed.add_field(
                name=f"**{question}**",
                value="[yes (**y**) / no (**n**) / idk (**i**) / probably (**p**) / probably not (**pn**)]\
                    \n[back (**b**)]\
                    \n[stop (**s**)]",
            )
            await ctx.reply(embed=embed)

            try:
                answer_message = await self.bot.wait_for(
                    "message", check=check, timeout=30
                )
            except asyncio.TimeoutError:
                raise AkiError("You didn't respond in time!")
            if answer_message.content.lower() in AKINATOR_RESPONSES.get("stop"):
                await ctx.reply("Aki stopped!")
                return
            if answer_message.content.lower() in AKINATOR_RESPONSES.get("back"):
                question = await akinator.back()
                index -= 1
            else:
                question = await akinator.answer(answer_message.content)
                index += 1

        await akinator.win()

        embed = Embed(
            title=akinator.first_guess["name"], color=Color(random.randint(0, 0xFFFFFF))
        )

        embed.set_image(url=akinator.first_guess["absolute_picture_path"])
        embed.add_field(name="From", value=akinator.first_guess["description"])
        embed.set_footer(text="Was I Correct? | y/yes/n/no")

        await ctx.reply(embed=embed)

        def confirmation_check(message: Message):
            return message.channel == ctx.channel and message.author == ctx.author

        try:
            confirmation_message = await self.bot.wait_for(
                "message", check=confirmation_check, timeout=10
            )
            response = confirmation_message.content.lower()

            if response in AKINATOR_RESPONSES.get("yes"):
                await ctx.reply("I Guessed correct, Once Again")
            elif response in AKINATOR_RESPONSES.get("no"):
                await ctx.reply("I have been defeated. You Win.")
            else:
                await ctx.reply(
                    "I don't know what that means but I'll take it as a win "
                )
        except TimeoutError:
            raise AkiError("You didn't respond in time!")

    @commands.command()
    async def emojify(self, ctx: Context, *, word: str):
        num2words = {
            0: "zero",
            1: "one",
            2: "two",
            3: "three",
            4: "four",
            5: "five",
            6: "six",
            7: "seven",
            8: "eight",
            9: "nine",
        }
        word = word.lower()

        if not word:
            return

        emojified = ""
        for letter in word:
            if letter == " ":
                emojified += "    "
            elif letter.isalpha():
                emoji = f":regional_indicator_{letter}: "
                emojified += emoji
            elif letter.isdigit():
                letter = int(letter)
                emoji = num2words[letter]
                emojified += f":{emoji}: "
            else:
                emojified += letter

        await ctx.reply(emojified)


def setup(bot):
    bot.add_cog(Misc(bot))
