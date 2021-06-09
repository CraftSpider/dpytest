
import pytest
import discord.ext.test as test


@pytest.mark.asyncio
async def test_edit(bot):
    guild = bot.guilds[0]
    channel = guild.channels[0]

    mes = await channel.send("Test Message")
    await mes.edit(content="New Message")

    assert mes.content == "New Message"
