import pytest
import discord
import discord.ext.test as dpytest  # noqa: F401
from discord.utils import get


@pytest.mark.asyncio
async def test_get_channel(bot: discord.Client) -> None:
    guild = bot.guilds[0]
    channel_0 = guild.channels[0]

    channel_get = get(guild.channels, name=channel_0.name)

    assert channel_0 == channel_get


@pytest.mark.asyncio
async def test_get_channel_history(bot: discord.Client) -> None:
    guild = bot.guilds[0]
    channel_0 = guild.channels[0]

    channel_get: discord.TextChannel | None = get(guild.channels, name=channel_0.name)  # type: ignore[assignment]

    assert channel_0 == channel_get

    test_message = await channel_get.send("Test Message")

    channel_history = [msg async for msg in channel_get.history(limit=10)]

    assert test_message in channel_history
