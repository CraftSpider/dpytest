from discord.ext import commands


class Greeting(commands.Cog):

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.text_channels[0]
        if channel is not None:
            await channel.send('Welcome {0.mention}.'.format(member))


def setup(bot):
    bot.add_cog(Greeting())
