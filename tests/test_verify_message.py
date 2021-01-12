import discord
import pytest
import discord.ext.test as dpytest


@pytest.mark.asyncio
async def test_message_equals(bot):
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    await channel.send("Test Message")
    dpytest.verify_message("Test Message")
    await dpytest.empty_queue()


@pytest.mark.asyncio
async def test_message_not_equals(bot):
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    await channel.send("You shall pass !!")
    dpytest.verify_message("You shall not pass !!", equals=False)
    await dpytest.empty_queue()


@pytest.mark.asyncio
async def test_message_contains_true(bot):
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    await channel.send("Very long message talking about Foobar")
    dpytest.verify_message("Foobar", contains=True)
    await dpytest.empty_queue()


@pytest.mark.asyncio
async def test_message_contains_false(bot):
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    await channel.send("Very long message talking about Foobar")
    dpytest.verify_message("Barfoo", equals=False, contains=True)
    await dpytest.empty_queue()


@pytest.mark.asyncio
async def test_message_assert_nothing(bot):

    dpytest.verify_message(assert_nothing=True)
    await dpytest.empty_queue()


@pytest.mark.asyncio
async def test_message_peek(bot):
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    await channel.send("Hello, world !")
    # peek option doesn't remove the message fro the queue
    dpytest.verify_message("Hello, world !", peek=True)
    # verify_message (without peek) WILL remove message from the queue
    dpytest.verify_message("Hello, world !")
    await dpytest.empty_queue()
