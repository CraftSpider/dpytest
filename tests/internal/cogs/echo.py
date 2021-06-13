from discord.ext.commands import Cog, command


class Echo(Cog):

    # Silence the default on_error handler
    async def cog_command_error(self, ctx, error):
        pass

    @command()
    async def echo(self, ctx, text: str):
        await ctx.send(text)


def setup(bot):
    bot.add_cog(Echo())
