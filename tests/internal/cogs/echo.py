from discord.ext import commands
from discord.ext.commands._types import BotT
from discord.ext.commands import Cog, command


class Echo(Cog):

    # Silence the default on_error handler
    async def cog_command_error(self, ctx: commands.Context[BotT], error: Exception) -> None:
        pass

    @command()
    async def echo(self, ctx: commands.Context[BotT], *, text: str) -> None:
        await ctx.send(text)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Echo())
