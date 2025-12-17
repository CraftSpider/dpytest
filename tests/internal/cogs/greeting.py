import discord
from discord.ext import commands


class Greeting(commands.Cog):

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        channel = member.guild.text_channels[0]
        if channel is not None:
            await channel.send(f"Welcome {member.mention}.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Greeting())
