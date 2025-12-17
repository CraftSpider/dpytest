import discord
import pytest
import discord.ext.test as dpytest


@pytest.mark.asyncio
async def test_verify_activity_matches(bot: discord.Client) -> None:
    fake_act = discord.Activity(name="Streaming",
                                url="http://mystreamingfeed.xyz",
                                type=discord.ActivityType.streaming)
    await bot.change_presence(activity=fake_act)
    assert dpytest.verify().activity().matches(fake_act)

    other_act = discord.Activity(name="Playing Around", type=discord.ActivityType.playing)
    await bot.change_presence(activity=other_act)
    assert not dpytest.verify().activity().matches(fake_act)


@pytest.mark.asyncio
async def test_verify_no_activity(bot: discord.Client) -> None:
    await bot.change_presence(activity=None)
    assert dpytest.verify().activity().matches(None)
