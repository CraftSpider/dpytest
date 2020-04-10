
import pytest
import discord.ext.test as test


@pytest.mark.asyncio
async def test_user_mention(bot):
    guild = bot.guilds[0]
    mes = await test.message(f"<@{guild.me.id}>")

    assert len(mes.mentions) == 1
    assert mes.mentions[0] == guild.me

    mes = await test.message("Not a mention in sight")

    assert len(mes.mentions) == 0


@pytest.mark.asyncio
async def test_role_mention(bot):
    guild = bot.guilds[0]
    role = await guild.create_role(name="Test Role")
    mes = await test.message(f"<@&{role.id}>")

    assert len(mes.role_mentions) == 1
    assert mes.role_mentions[0] == role

    mes = await test.message("Not a mention in sight")

    assert len(mes.role_mentions) == 0


@pytest.mark.asyncio
async def test_channel_mention(bot):
    guild = bot.guilds[0]
    channel = guild.channels[0]
    mes = await test.message(f"<#{channel.id}>")

    assert len(mes.channel_mentions) == 1
    assert mes.channel_mentions[0] == channel

    mes = await test.message("Not a mention in sight")

    assert len(mes.channel_mentions) == 0
