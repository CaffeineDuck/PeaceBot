from typing import List

import discord
from discord import Member, Embed, Color
from discord.ext import commands

from bot.utils.hangman import Hanger, HangMan


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """
    Tic Tac Toe
    """
    # Map integer value to emoji to send in discord
    INT_TO_EMOJI = {
        -1: ':regional_indicator_o:',
        0: ':stop_button:',
        1: ':regional_indicator_x:'
    }

    def create_embed(self, game_state: List[List[int]], status: str):
        """
        Creates the game embed when given gamestate and status string
        """
        game = Embed(title="Tic-Tac-Toe", color=Color.blurple())
        game_str = "\n".join(["".join([self.INT_TO_EMOJI[i] for i in line])
                              for line in game_state])

        game.add_field(name="GameBoard", value=game_str, inline=False)
        game.add_field(name="Status", value=status, inline=False)

        return game

    def is_game_over(self, game_state: List[List[int]]):
        """
        Checks whether someone has won the game
        """
        for i in game_state:
            row_sum = sum(i)
            if row_sum == -3:
                return True
            elif row_sum == 3:
                return True

        for i in range(3):
            col_sum = game_state[0][i]+game_state[1][i]+game_state[2][i]
            if col_sum == -3 or col_sum == 3:
                return True

        cross_sum1 = game_state[0][0] + game_state[1][1] + game_state[2][2]
        cross_sum2 = game_state[2][0] + game_state[1][1] + game_state[0][2]

        if cross_sum1 == -3 or cross_sum2 == -3 or cross_sum1 == 3 or cross_sum2 == 3:
            return True

        return False

    @commands.command(name="noughts", aliases=["tictactoe"])
    async def noughts_game(self, ctx: commands.Context, player2: Member):
        """
        Play noughts/tic-tac-toe with your friends!
        """

        player1 = ctx.author
        current_player = player1

        game_state = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

        game = self.create_embed(
            game_state, f"Current move: {current_player.name}")

        game_msg = await ctx.send(embed=game)

        def check(m: Message):
            # Make sure message is from the same channel
            if m.channel != ctx.channel:
                return False
            # Make sure message is from current player
            if m.author != current_player:
                return False
            # Make sure message is entirely numeric
            if not m.content.isdigit():
                return False

            # Get the target position the player wants to check
            move_box = int(m.content) - 1
            # Check if it's within range
            if move_box < 0 or move_box > 8:
                return False
            # Get row and column number
            row = move_box//3
            col = move_box % 3
            # If that target position is not 0 then do nothing
            if game_state[row][col]:
                return False

            # Mutate game state accordingly
            game_state[row][col] = 1 if current_player == player1 else -1

            return True

        for i in range(9):
            try:
                m = await self.bot.wait_for('message', check=check, timeout=30)
            except asyncio.TimeoutError:
                await game_msg.edit(embed=self.create_embed(gamestate, f"{current_player.name} failed to move"))
                return
            else:
                # Delete the message sent by the user
                await m.delete()
                game_over = self.is_game_over(game_state)
                # End if game is over
                if game_over:
                    game = self.create_embed(
                        game_state, f"{current_player.name} won!")
                    await game_msg.edit(embed=game)
                    return

                current_player = player1 if current_player == player2 else player2
                game = self.create_embed(
                    game_state, f"Current move: {current_player.name}")
                await game_msg.edit(embed=game)

        await game_msg.edit(embed=self.create_embed(game_state, "It's a draw!"))


    """
    HangMan
    """

    @commands.command(name='hangman')
    @commands.guild_only()
    async def start_hangman(self, ctx):
        """
        Play Hangman with your friends
        """
        game_msg = await ctx.channel.send(f"{ctx.message.author} has opened a game of hangman! React below to join. {ctx.message.author.mention}, the game will start when you type \"start game\"")
        await game_msg.add_reaction('✅')

        async def wait_for_game_start():
            def check(msg):
                if msg.author.id != ctx.message.author.id:
                    return False
                if msg.content.lower() not in ["start game", "cancel"]:
                    return False
                if msg.channel.id != ctx.channel.id:
                    return False
                return True

            try:
                msg = await self.bot.wait_for('message', check=check, timeout=600)
            except asyncio.TimeoutError:
                await ctx.send("Game timed out")
            if msg.content.lower() == 'cancel':
                await ctx.send("Game Cancelled")
                return []
            users = set()
            update_msg = await ctx.channel.fetch_message(game_msg.id)
            for reaction in update_msg.reactions:
                async for user in reaction.users():
                    if not user.bot:
                        users.add(user.id)
            users.add(ctx.message.author.id)
            num_users = len(users)
            if num_users < 2:
                await ctx.send(f"There are not enough people to play. Minimum is 2, and you only have {num_users}.")
                return await wait_for_game_start()
            return users

        users = await wait_for_game_start()
        if users == []:
            return
        members = []
        for user_id in users:
            member = ctx.guild.get_member(user_id)
            members.append(member)
        await ctx.send("Starting Game")

        game = HangMan(members, self.bot, ctx.channel)
        await game.play()

    
def setup(bot: commands.Bot):
    bot.add_cog(Games(bot))