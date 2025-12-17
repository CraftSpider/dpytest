import pytest
import discord
import discord.ext.test as dpytest  # noqa: F401


@pytest.mark.asyncio
async def test_get_message(bot: discord.Client) -> None:
    guild = bot.guilds[0]
    channel: discord.TextChannel = guild.channels[0]  # type: ignore[assignment]

    message = await channel.send("Test Message")
    message2 = await channel.fetch_message(message.id)

    assert message.id == message2.id

    with pytest.raises(discord.NotFound):
        await channel.fetch_message(0xBADBEEF)
