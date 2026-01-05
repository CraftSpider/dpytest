from datetime import timedelta

import discord
from discord.ext import commands
from discord.ext.commands._types import BotT
from discord.ext.commands import Cog, command


class Misc(Cog):
    @command()
    async def pollme(self, ctx: commands.Context[BotT]) -> None:
        poll = discord.Poll(question="Test?", duration=timedelta(hours=1))
        poll.add_answer(text="Yes")
        poll.add_answer(text="No")
        await ctx.send("Poll test", poll=poll)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Misc())
