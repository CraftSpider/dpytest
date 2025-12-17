from pathlib import Path
import discord
import pytest
import discord.ext.test as dpytest


@pytest.mark.asyncio
async def test_verify_file_text(bot: discord.Client) -> None:
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    path_ = Path(__file__).resolve().parent / 'data/loremimpsum.txt'
    file_ = discord.File(path_)
    await channel.send(file=file_)
    assert dpytest.verify().message().attachment(path_)


@pytest.mark.asyncio
async def test_verify_file_jpg(bot: discord.Client) -> None:
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    path_ = Path(__file__).resolve().parent / 'data/unit-tests.jpg'
    file_ = discord.File(path_)
    await channel.send(file=file_)
    assert dpytest.verify().message().attachment(path_)


@pytest.mark.asyncio
async def test_verify_file_KO(bot: discord.Client) -> None:
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    path_ = Path(__file__).resolve().parent / 'data/unit-tests.jpg'
    file_ = discord.File(path_)
    await channel.send(file=file_)
    path2 = Path(__file__).resolve().parent / 'data/loremimpsum.txt'
    assert not dpytest.verify().message().attachment(path2)
