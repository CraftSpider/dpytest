from discord.ext.commands import Cog, command


class Echo(Cog):
    @command()
    async def echo(self, ctx, text: str):
        await ctx.send(text)


def setup(bot):
    bot.add_cog(Echo())
