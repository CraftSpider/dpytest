import pytest


@pytest.mark.asyncio
async def test_bot_join_voice(bot):
    assert not bot.voice_clients
    await bot.guilds[0].voice_channels[0].connect()
    assert bot.voice_clients


@pytest.mark.asyncio
async def test_bot_leave_voice(bot):
    voice_client = await bot.guilds[0].voice_channels[0].connect()
    await voice_client.disconnect()
    assert not bot.voice_clients


@pytest.mark.asyncio
async def test_move_member(bot):
    guild = bot.guilds[0]
    voice_channel = guild.voice_channels[0]
    member = guild.members[0]

    assert member.voice is None
    await member.move_to(voice_channel)
    assert member.voice.channel == voice_channel

    await member.move_to(None)
    assert member.voice is None
