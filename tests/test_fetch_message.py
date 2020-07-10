import pytest
import discord
import discord.ext.test as dpytest


@pytest.mark.asyncio
async def test_get_message(bot):
    guild = bot.guilds[0]
    channel = guild.channels[0]

    message = await channel.send("Test Message")
    message2 = await channel.fetch_message(message.id)

    assert message.id == message2.id

    with pytest.raises(discord.NotFound):
        await channel.fetch_message(0xBADBEEF)

    await dpytest.empty_queue()
