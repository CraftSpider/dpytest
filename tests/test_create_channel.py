import pytest
import discord
import discord.ext.test as dpytest


@pytest.mark.asyncio
async def test_create_voice_channel(bot):
    guild = bot.guilds[0]
    http = bot.http

    # create_channel checks the value of variables in the parent call context, so we need to set these for it to work
    self = guild  # noqa: F841
    name = "voice_channel_1"
    channel = await http.create_channel(guild, channel_type=discord.ChannelType.voice.value)
    assert channel['type'] == discord.ChannelType.voice.value
    assert channel['name'] == name


@pytest.mark.asyncio
async def test_make_voice_channel(bot):
    guild = bot.guilds[0]
    bitrate = 100
    user_limit = 5
    channel = dpytest.backend.make_voice_channel("voice", guild, bitrate=bitrate, user_limit=user_limit)
    assert channel.name == "voice"
    assert channel.guild == guild
    assert channel.bitrate == bitrate
    assert channel.user_limit == user_limit
