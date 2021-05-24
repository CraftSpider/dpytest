
import pytest
import discord.ext.test as test


@pytest.mark.asyncio
async def test_dm_send(bot):
    guild = bot.guilds[0]
    await guild.members[0].send("hi")

    assert test.verify().message().content("hi")


@pytest.mark.asyncio
@pytest.mark.cogs("cogs.echo")
async def test_dm_message(bot):
    guild = bot.guilds[0]
    member = guild.members[0]
    dm = await member.create_dm()
    await test.message("!echo Ah-Ha!", dm)

    assert test.verify().message().content("Ah-Ha!")
