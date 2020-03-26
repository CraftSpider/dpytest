import discord
from discord.ext.commands import Bot, Cog, command, Context


class Echo(Cog):
    @command()
    async def echo(self, ctx: Context, text: str):
        await ctx.send(text)


def setup(bot: Bot):
    bot.add_cog(Echo())
