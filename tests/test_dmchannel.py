import discord
import pytest
import discord.ext.test as dpytest


@pytest.mark.asyncio
async def test_dm_send(bot: discord.Client) -> None:
    guild = bot.guilds[0]
    await guild.members[0].send("hi")

    assert dpytest.verify().message().content("hi")


@pytest.mark.asyncio
@pytest.mark.cogs("cogs.echo")
async def test_dm_message(bot: discord.Client) -> None:
    guild = bot.guilds[0]
    member = guild.members[0]
    dm = await member.create_dm()
    await dpytest.message("!echo Ah-Ha!", dm)

    assert dpytest.verify().message().content("Ah-Ha!")
