import pytest
import discord
import discord.ext.test as dpytest
from discord import PermissionOverwrite
from discord.ext.commands import Bot


@pytest.mark.asyncio
async def test_permission_setting(bot):
    """tests, that the framework sets overrides correctly"""
    g = bot.guilds[0]
    c = g.text_channels[0]
    m = g.members[0]

    await dpytest.set_permission_overrides(g.me, c, manage_roles=False)
    with pytest.raises(discord.errors.DiscordException):
        await c.set_permissions(m, send_messages=False, read_messages=True)

    await dpytest.set_permission_overrides(g.me, c, manage_roles=True)
    perm = c.permissions_for(g.me)
    assert perm.manage_roles is True

    await c.set_permissions(m, send_messages=False, read_messages=True, ban_members=False)
    perm = c.permissions_for(m)
    assert perm.read_messages is True
    assert perm.send_messages is False
    assert perm.ban_members is False

    await c.set_permissions(m, send_messages=False, read_messages=True, ban_members=True)
    perm = c.permissions_for(m)
    assert perm.ban_members is True

    await dpytest.set_permission_overrides(g.me, c, manage_roles=False, administrator=True)
    await c.set_permissions(m, ban_members=False, kick_members=True)
    perm = c.permissions_for(m)
    assert perm.kick_members is True
    assert perm.ban_members is False


@pytest.mark.asyncio
@pytest.mark.cogs("cogs.echo")
async def test_bot_send_not_allowed(bot):
    """tests, that a bot gets an Exception, if not allowed to send a message"""
    g = bot.guilds[0]
    c = g.text_channels[0]

    await dpytest.set_permission_overrides(g.me, c, send_messages=False)
    with pytest.raises(discord.ext.commands.errors.CommandInvokeError):
        await dpytest.message("!echo hello", channel=c)

    assert dpytest.sent_queue.empty()

    perm = PermissionOverwrite(send_messages=True, read_messages=True)
    await dpytest.set_permission_overrides(g.me, c, perm)
    await dpytest.message("!echo hello", channel=c)
    assert dpytest.verify().message().content("hello")
