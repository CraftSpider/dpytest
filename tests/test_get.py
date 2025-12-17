import discord
import pytest
import discord.ext.test as dpytest


@pytest.mark.asyncio
async def test_get_message(bot: discord.Client) -> None:
    """Dont use this in your code, it's just dummy test.
    Use verify_message() instead of 'get_message' and 'message.content'
    """
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    await channel.send("Test Message")
    mess = dpytest.get_message()
    assert mess.content == "Test Message"


@pytest.mark.asyncio
async def test_get_message_peek(bot: discord.Client) -> None:
    """Dont use this in your code, it's just dummy test.
    Use verify_message() instead of 'get_message' and 'message.content'
    """
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    await channel.send("Test Message Peek")
    mess = dpytest.get_message(peek=True)  # peek doesnt remove the message from the queue
    assert mess.content == "Test Message Peek"


@pytest.mark.asyncio
async def test_get_embed(bot: discord.Client) -> None:
    """Dont use this in your code, it's just dummy test.
    Use verify_embed() instead of 'get_embed'
    """
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    embed = discord.Embed(title="Test Embed")
    embed.add_field(name="Field 1", value="Lorem ipsum")

    await channel.send(embed=embed)
    emb = dpytest.get_embed()
    assert emb == embed


@pytest.mark.asyncio
async def test_get_embed_peek(bot: discord.Client) -> None:
    """Dont use this in your code, it's just dummy test.
    Use verify_embed() instead of 'get_embed'
    """
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    embed = discord.Embed(title="Test Embed")
    embed.add_field(name="Field 1", value="Lorem ipsum")

    await channel.send(embed=embed)
    emb = dpytest.get_embed(peek=True)
    assert emb == embed
