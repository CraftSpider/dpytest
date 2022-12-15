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
async def test_edit_role(bot):
    await test_add_role(bot=bot)
    await bot.guilds[0].create_role(name="TestRole")  # Role object
    assert len(bot.guilds[0].roles) == 3
    staff_role = bot.guilds[0].roles[1]
    await staff_role.edit(
        permissions=discord.Permissions(8), colour=discord.Color.red(),
        hoist=True, mentionable=True, position=2
    )
    assert bot.guilds[0].roles[2] == staff_role
    assert bot.guilds[0].roles[2].colour == discord.Color.red()
    assert bot.guilds[0].roles[2].hoist is True
    assert bot.guilds[0].roles[2].mentionable is True
    assert bot.guilds[0].roles[2].permissions.administrator is True
    # assert staff_role in member1.roles


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
