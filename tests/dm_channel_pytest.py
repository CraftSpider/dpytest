import discord
import pytest
from discord import DMChannel, Guild, Member, TextChannel, User
from discord.ext.commands import Bot

from ..discord.ext.test import runner


@pytest.mark.asyncio
async def test_can_send_dm():
    """
    Tests, that a message directly can be sent to a user/member.
    Discord creates a DM Channel in the background
    """
    bot = Bot("!")
    runner.configure(bot)
    g: Guild = bot.guilds[0]
    m: Member = g.members[0]
    assert isinstance(m, discord.abc.User), "participant must be a user (not channel)"
    await m.send("this is a dm!")
    runner.verify_message("this is a dm!")


@pytest.mark.asyncio
async def test_bot_can_receive_dm():
    """
    Tests, that a bot can receive a message directly from a user/member
    """
    bot = Bot("!")
    bot.load_extension('tests.internal.cogs.echo')
    runner.configure(bot)
    g: Guild = bot.guilds[0]
    m: User = g.members[0]
    assert isinstance(m, discord.abc.User), "participant must be a user (not channel)"
    dm = m.dm_channel or (await m.create_dm())
    assert dm
    assert isinstance(dm, DMChannel)
    await runner.message("!origin_channel_type", channel=dm, member=m)
    runner.verify_message(str(DMChannel))

@pytest.mark.asyncio
async def test_bot_receive_guild_reply_dm():
    """
    Tests, that a bot can receive a message in a guild,
    and directly reply to a user/member via dm
    """
    bot = Bot("!")
    bot.load_extension('tests.internal.cogs.echo')
    runner.configure(bot)
    g: Guild = bot.guilds[0]
    m: User = g.members[0]
    c: TextChannel = g.channels[0]
    await runner.message("!echo_dm this is a dm reply!", channel=c, member=m)
    assert isinstance(m, discord.abc.User), "participant must be a user (not channel)"
    runner.verify_message("this is a dm reply!")
