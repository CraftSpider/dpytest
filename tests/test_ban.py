
import pytest
import discord
import discord.ext.test as dpytest

@pytest.mark.asyncio
async def test_ban_user(bot: discord.Client):
    guild = bot.guilds[0]
    member = guild.members[0]
    await guild.ban(member)

    assert guild.get_member(member.id) is None


@pytest.mark.asyncio
async def test_unban_user(bot: discord.Client):
    guild = bot.guilds[0]
    member = guild.members[0]
    await guild.ban(member)
    await guild.unban(member)
