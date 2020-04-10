import pytest
import discord
from discord import PermissionOverwrite
from discord.ext.commands import Bot
from discord.ext.test import runner


@pytest.mark.asyncio
async def test_permission_setting(bot):
    """tests, that the framework sets overrides correctly"""
    g = bot.guilds[0]
    c = g.text_channels[0]
    m = g.members[0]

    await runner.set_permission_overrides(g.me, c, manage_roles=False)
    with pytest.raises(discord.errors.DiscordException):
        await c.set_permissions(m, send_messages=False, read_messages=True)

    await runner.set_permission_overrides(g.me, c, manage_roles=True)
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

    await runner.set_permission_overrides(g.me, c, manage_roles=False, administrator=True)
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

    await runner.set_permission_overrides(g.me, c, send_messages=False)
    with pytest.raises(discord.ext.commands.errors.CommandInvokeError):
        await runner.message("!echo hello", channel=c)

    assert runner.sent_queue.empty()

    perm = PermissionOverwrite(send_messages=True, read_messages=True)
    await runner.set_permission_overrides(g.me, c, perm)
    await runner.message("!echo hello", channel=c)
    runner.verify_message("hello")
