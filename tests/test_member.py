import pytest
import discord.ext.test as dpytest


@pytest.mark.asyncio
@pytest.mark.cogs("cogs.greeting")
async def test_member_join(bot):
    """Dont use this in your code, it's just dummy test.
    Use verify_message() instead of 'get_message' and 'message.content'
    """
    guild = bot.guilds[0]
    member_count = len(guild.members)

    await dpytest.member_join(name="Foo", discrim=5)
    new_member = guild.members[member_count]

    assert len(guild.members) == member_count + 1
    assert new_member.name == "Foo"
    assert new_member.discriminator == "0005"

    await dpytest.run_all_events()  # requires for the cov Greeting listner to be executed  # noqa: E501

    assert dpytest.verify().message().content(f"Welcome {new_member.mention}.")
