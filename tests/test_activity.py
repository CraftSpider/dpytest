import discord
import pytest
import discord.ext.test as dpytest


@pytest.mark.asyncio
async def test_verify_activity(bot):
    fake_act = discord.Activity(name="Streaming",
                                url="http://mystreamingfeed.xyz",
                                type=discord.ActivityType.streaming)

    await bot.change_presence(activity=fake_act)

    dpytest.verify_activity(fake_act)
    await dpytest.empty_queue()

