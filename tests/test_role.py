import discord
import pytest
import discord.ext.test as dpytest


@pytest.mark.asyncio
async def test_add_role(bot):
    guild = bot.guilds[0]
    staff_role = await guild.create_role(name="Staff")  # Role object
    member1 = guild.members[0]  # Member

    await dpytest.add_role(member1, staff_role)
    assert staff_role in member1.roles


@pytest.mark.asyncio
async def test_remove_role(bot):
    guild = bot.guilds[0]
    staff_role = await guild.create_role(name="Staff")  # Role object
    member1 = guild.members[0]  # Member

    # First, we use add_role
    await dpytest.add_role(member1, staff_role)
    assert staff_role in member1.roles

    # then remove_role
    await dpytest.remove_role(member1, staff_role)
    assert staff_role not in member1.roles


@pytest.mark.asyncio
async def test_remove_role2(bot):
    guild = bot.guilds[0]
    staff_role = await guild.create_role(name="Staff")  # Role object

    # First, we use add_role
    await dpytest.add_role(0, staff_role)
    assert staff_role in guild.members[0].roles

    # then remove_role
    await dpytest.remove_role(0, staff_role)
    assert staff_role not in guild.members[0].roles
