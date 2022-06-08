
import pytest
import discord.ext.test as test

@pytest.mark.asyncio
async def test_edit(bot):
    guild = bot.guilds[0]
    channel = guild.channels[0]

    mes = await channel.send("Test Message")
    await mes.edit(content="New Message")

    assert mes.content == "New Message"

@pytest.mark.asyncio
@pytest.mark.cogs("cogs.edit")
async def test_edit_cog(bot):
    guild = bot.guilds[0]
    member = guild.members[0]
    dm = await member.create_dm()
    await test.message("!edit Ah-Ha!", dm)

    assert test.verify().message().content("Ah-Ha!")
    assert test.verify().message().content("!aH-hA")
