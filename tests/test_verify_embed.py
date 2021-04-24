import discord
import pytest
import discord.ext.test as dpytest


@pytest.mark.asyncio
async def test_embed(bot):
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    embed = discord.Embed(title="Test Embed")
    embed.add_field(name="Field 1", value="Lorem ipsum")
    
    embed2 = embed = discord.Embed(title="Test Embed")
    embed2.add_field(name="Field 1", value="Lorem ipsum")

    await channel.send(embed=embed)
    dpytest.verify_embed(embed2)
    await dpytest.empty_queue()


@pytest.mark.asyncio
async def test_embed_KO(bot):
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    embed = discord.Embed(title="Test Embed")
    embed.add_field(name="Field 1", value="Lorem ipsum")
    
    embed2 = discord.Embed(title="Test Embed KO")
    embed2.add_field(name="Field 35", value="Foo Bar")

    await channel.send(embed=embed)
    dpytest.verify_embed(embed2, equals=False)
    await dpytest.empty_queue()


@pytest.mark.asyncio
async def test_embed_assert_nothing(bot):

    dpytest.verify_embed(assert_nothing=True)
    await dpytest.empty_queue()


@pytest.mark.asyncio
async def test_embed_peek(bot):
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    embed = discord.Embed(title="Test Embed")
    embed.add_field(name="Field 1", value="Lorem ipsum")
    
    embed2 = embed = discord.Embed(title="Test Embed")
    embed2.add_field(name="Field 1", value="Lorem ipsum")

    await channel.send(embed=embed)

    # peek option doesn't remove the message fro the queue
    dpytest.verify_embed(embed2, peek=True)
    # verify_embed (without peek) WILL remove emebd from the queue
    dpytest.verify_embed(embed2)
    await dpytest.empty_queue()
