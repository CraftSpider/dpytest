
import pytest
import discord.ext.test as test


@pytest.mark.asyncio
async def test_dm(bot):
    guild = bot.guilds[0]
    await guild.members[0].send("hi")

    test.verify_message("hi")
