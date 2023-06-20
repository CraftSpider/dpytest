import pytest
import discord.ext.test as dpytest
from discord.ext.test.easy_verify import assert_easy_message_content


@pytest.mark.asyncio
@pytest.mark.cogs("cogs.echo")
async def test_echo(bot):
    await dpytest.message("!echo Hello")
    assert_easy_message_content("Good morning")
