from pathlib import Path
import discord
import pytest
import discord.ext.test as dpytest


@pytest.mark.skip(reason="verify_file assert == beween files doesn't work")
@pytest.mark.asyncio
async def test_verify_file(bot):
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    path_ = Path(__file__).resolve().parent / 'loremimpsum.txt'
    file_ = discord.File(path_)
    await channel.send(file=file_)
    dpytest.verify_file(file_)
    await dpytest.empty_queue()
