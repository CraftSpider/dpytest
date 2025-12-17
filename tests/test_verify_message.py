import discord  # noqa: F401
import pytest
import discord.ext.test as dpytest


@pytest.mark.asyncio
async def test_message_equals(bot: discord.Client) -> None:
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    await channel.send("Test Message")
    assert dpytest.verify().message().content("Test Message")


@pytest.mark.asyncio
async def test_message_not_equals(bot: discord.Client) -> None:
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    await channel.send("You shall pass !!")
    assert not dpytest.verify().message().content("You shall not pass !!")


@pytest.mark.asyncio
async def test_message_contains_true(bot: discord.Client) -> None:
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    await channel.send("Very long message talking about Foobar")
    assert dpytest.verify().message().contains().content("Foobar")


@pytest.mark.asyncio
async def test_message_contains_false(bot: discord.Client) -> None:
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    await channel.send("Very long message talking about Foobar")
    assert not dpytest.verify().message().contains().content("Barfoo")


@pytest.mark.asyncio
async def test_message_assert_nothing(bot: discord.Client) -> None:
    assert dpytest.verify().message().nothing()


@pytest.mark.asyncio
async def test_message_peek(bot: discord.Client) -> None:
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    await channel.send("Hello, world !")
    # peek option doesn't remove the message fro the queue
    assert dpytest.verify().message().peek().content("Hello, world !")
    # verify_message (without peek) WILL remove message from the queue
    assert dpytest.verify().message().content("Hello, world !")
