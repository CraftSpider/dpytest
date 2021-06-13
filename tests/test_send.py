import discord
import pytest
import discord.ext.test as dpytest


@pytest.mark.asyncio
async def test_message(bot):
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    await channel.send("Test Message")


@pytest.mark.asyncio
async def test_embed(bot):
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    embed = discord.Embed(title="Test Embed")
    embed.add_field(name="Field 1", value="Lorem ipsum")

    await channel.send(embed=embed)
