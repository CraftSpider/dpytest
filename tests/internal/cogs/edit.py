from discord.ext.commands import Cog, command
from asyncio import sleep


class Edit(Cog):

    # Silence the default on_error handler
    async def cog_command_error(self, ctx, error):
        pass

    @command()
    async def edit(self, ctx, text: str):
        msg = await ctx.send(text)
        print("Something")
        reversed = text[::-1]
        response = await msg.edit(content=reversed)  # reverse the output of the command



def setup(bot):
    bot.add_cog(Edit())
