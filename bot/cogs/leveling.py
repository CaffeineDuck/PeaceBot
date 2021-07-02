import random
from typing import Optional, Text, Union

import discord
from discord.ext import commands
from discord.ext.commands import BucketType, Greedy

from bot.bot import PeaceBot
from bot.utils.leveling_handler import LevelingHandler, UserRank
from bot.utils.mixins.better_cog import BetterCog
from models import LevelingUserModel


class LevelingError(commands.CommandError):
    pass


class Leveling(BetterCog):
    def __init__(self, bot: PeaceBot):
        super().__init__(bot)
        self._cd = commands.CooldownMapping.from_cooldown(
            1, 60, commands.BucketType.member
        )
        self.leveling_handler = LevelingHandler(self.bot)

    def get_ratelimit(self, message: discord.Message) -> Optional[int]:
        """Returns the ratelimit left"""
        bucket = self._cd.get_bucket(message)
        return bucket.update_rate_limit()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        ratelimit = self.get_ratelimit(message)
        if ratelimit or message.author.bot or not message.guild:
            return
        await self.leveling_handler.handle_user_message(message)

    @commands.Cog.listener()
    async def on_user_level_up(self, user_model: LevelingUserModel):
        if user_model.level == 1:
            return

        leveling_channel = self.bot.get_channel(user_model.defualt_rank_channel)
        guild: discord.Guild = self.bot.get_guild(user_model.guild_id)
        member = guild.get_member(user_model.user_id)

        await leveling_channel.send(
            f"GG {member.mention} has advanced to **Level {user_model.level}**"
        )

    @commands.cooldown(1, 5, BucketType.user)
    @commands.command()
    async def rank(self, ctx: commands.Context, member: Optional[discord.Member]):
        member = member or ctx.author
        user_rank: UserRank = await self.leveling_handler.get_user_rank(member)

        embed = discord.Embed(
            title=f"**{member}**'s Rank",
            description=f"Here is a summary of {member.mention}'s rank!",
            color=discord.Color(random.randint(0, 0xFFFFFF)),
            timestamp=ctx.message.created_at,
        )
        embed.add_field(name="Position", value=f"#{user_rank.position}", inline=False)
        embed.add_field(name="Level", value=user_rank.level, inline=False)
        embed.add_field(
            name="XP", value=f"{user_rank.xp}/{user_rank.required_xp}", inline=False
        )
        embed.add_field(name="Messages Sent", value=user_rank.messages, inline=False)

        await ctx.reply(embed=embed)

    @commands.command(aliases=["ipm6lv"])
    @commands.has_permissions(manage_guild=True)
    async def importmee6levels(self, ctx: commands.Context):
        await ctx.reply(
            "**Please Wait!** The wait time may vary according to the number of members in this server!"
        )
        async with ctx.typing():
            await self.leveling_handler.import_from_mee6(ctx.guild.id)
            await ctx.reply("**Mee6 Data has been imported!**")

    @commands.command(aliases=["lb", "top"])
    async def leaderboard(self, ctx: commands.Context):
        guild_model = self.bot.guilds_cache.get(ctx.guild.id)
        user_models = (
            await LevelingUserModel.filter(guild=guild_model)
            .order_by("-xp")
            .prefetch_related("user")
            .limit(10)
        )
        ranks = "\n".join(
            [
                f"**{i+1}.** {ctx.guild.get_member(model.user.id)}"
                for (i, model) in enumerate(user_models)
            ]
        )
        ranks_embed = discord.Embed(
            title="LeaderBoard",
            description=ranks,
            color=discord.Color(random.randint(0, 0xFFFFFF)),
            timestamp=ctx.message.created_at,
        )
        await ctx.reply(embed=ranks_embed)

    @commands.guild_only()
    @commands.group("lvlcfg", invoke_without_command=True)
    async def leveling_config(self, ctx: commands.Context):
        """Configure the leveling system from this command"""
        await ctx.send_help(ctx.command)

    @leveling_config.command(name="toggle")
    async def leveling_guild_toggle(self, ctx: commands.Context, toggle: bool):
        model = await self.bot.get_guild_model(ctx.guild.id)
        model.leveling_enabled = toggle
        await model.save()
        self.bot.guilds_cache[ctx.guild.id] = model

        toggle_str = "enabled" if toggle else "disabled"
        await ctx.send(f"Leveling has been fully `{toggle_str}` in this guild!")

    @commands.has_permissions(manage_roles=True)
    @leveling_config.group(aliases=["rolerew"], invoke_without_command=True)
    async def role_rewards(self, ctx: commands.Context):
        """Configure rolerewards/ leveling based roles from here"""
        await ctx.send_help(ctx.command)

    @role_rewards.command(name="add")
    async def add_role_rewards(
        self, ctx: commands.Context, level: int, role: discord.Role
    ):
        """Add role rewards/ leveling based roles"""
        guild_model = await self.bot.get_guild_model(ctx.guild.id)

        old_role_rewards = guild_model.xp_role_rewards
        if not old_role_rewards:
            old_role_rewards = {}

        new_role_rewards = old_role_rewards | {level: role.id}
        guild_model.xp_role_rewards = new_role_rewards

        await guild_model.save()
        await ctx.reply(
            f"**Added** role rewards for level {level} with role `{role.name}`"
        )

    @role_rewards.command(name="remove", aliases=["rm"])
    async def remove_role_rewards(self, ctx: commands.Context, level: str):
        """Remove role rewards/ leveling based roles"""
        guild_model = await self.bot.get_guild_model(ctx.guild.id)
        role_rewards = guild_model.xp_role_rewards

        if not role_rewards:
            raise LevelingError("There are no role rewards setup!")

        removed_role_id = role_rewards.pop(level)
        removed_role = ctx.guild.get_role(removed_role_id)

        guild_model.xp_role_rewards = role_rewards

        await guild_model.save()
        await ctx.reply(
            f"**Removed** role rewards for level {level} with role `{removed_role.name}`"
        )

    @role_rewards.command(name="all", aliases=["list"])
    async def list_role_rewards(self, ctx: commands.Context):
        """Show all the role rewards/ leveling based roles"""
        guild_model = await self.bot.get_guild_model(ctx.guild.id)

        try:
            role_rewards_str = "\n".join(
                [
                    f"`{level}` -> {(ctx.guild.get_role(role_id)).mention}"
                    for (level, role_id) in guild_model.xp_role_rewards.items()
                ]
            )
        except AttributeError:
            role_rewards_str = "No role rewards setup!"

        embed = discord.Embed(
            title="Role Rewards",
            description=role_rewards_str,
            color=discord.Color(random.randint(0, 0xFFFFFF)),
        )
        await ctx.reply(embed=embed)

    @leveling_config.group(name="enable", invoke_without_command=True)
    async def leveling_enable(
        self, ctx: commands.Context, channels: Greedy[discord.TextChannel] = None
    ):
        """Enable leveling in given channels"""
        channels = channels or [ctx.channel]
        await self.leveling_handler.leveling_toggle_handler(channels, ctx, True)

    @leveling_enable.command(name="all")
    async def leveling_enable_all(self, ctx: commands.Context):
        await self.leveling_handler.leveling_toggle_handler("all", ctx, True)

    @leveling_config.group(name="disable", invoke_without_command=True)
    async def leveling_disable(
        self, ctx: commands.Context, channels: Greedy[discord.TextChannel] or str = None
    ):
        """Enable leveling in given channels"""
        channels = channels or [ctx.channel]
        await self.leveling_handler.leveling_toggle_handler(channels, ctx, False)

    @leveling_disable.command(name="all")
    async def leveling_disable_all(self, ctx: commands.Context):
        await self.leveling_handler.leveling_toggle_handler("all", ctx, False)


def setup(bot):
    bot.add_cog(Leveling(bot))
