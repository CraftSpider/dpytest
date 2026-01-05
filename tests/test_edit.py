import discord
import pytest
import discord.ext.test as dpytest  # noqa: F401
import discord.ext.commands as commands


@pytest.mark.asyncio
async def test_edit(bot: commands.Bot) -> None:
    guild = bot.guilds[0]
    channel = guild.channels[0]
    assert isinstance(channel, discord.TextChannel)

    mes = await channel.send("Test Message")
    persisted_mes1 = await channel.fetch_message(mes.id)
    edited_mes = await mes.edit(content="New Message")
    persisted_mes2 = await channel.fetch_message(mes.id)

    assert edited_mes.content == "New Message"
    assert persisted_mes1.content == "Test Message"
    assert persisted_mes2.content == "New Message"
