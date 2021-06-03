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
    assert dpytest.verify().message().embed(embed2)


@pytest.mark.asyncio
async def test_embed_KO(bot):
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    embed = discord.Embed(title="Test Embed")
    embed.add_field(name="Field 1", value="Lorem ipsum")
    
    embed2 = discord.Embed(title="Test Embed KO")
    embed2.add_field(name="Field 35", value="Foo Bar")

    await channel.send(embed=embed)
    assert not dpytest.verify().message().embed(embed2)


@pytest.mark.asyncio
async def test_embed_assert_nothing(bot):
    assert dpytest.verify().message().nothing()


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
    assert dpytest.verify().message().peek().embed(embed2)
    # verify_embed (without peek) WILL remove emebd from the queue
    assert dpytest.verify().message().embed(embed2)
