import discord
from discord.ext.commands import Bot, Cog, Context, command


class Echo(Cog):
    @command()
    async def echo(self, ctx: Context, *, text: str):
        await ctx.send(text)

    @command()
    async def echo_dm(self, ctx: Context, *, text: str):
        await ctx.author.send(text)

    @command()
    async def origin_channel_type(self, ctx: Context):
        await ctx.send(str(type(ctx.channel)))

def setup(bot: Bot):
    bot.add_cog(Echo())
