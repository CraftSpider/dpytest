import discord
import pytest
import discord.ext.test as dpytest


@pytest.mark.asyncio
async def test_member_join(bot):
    """Dont use this in your code, it's just dummy test.
    Use verify_message() instead of 'get_message' and 'message.content'
    """
    guild = bot.guilds[0]
    author: discord.Member = guild.members[0]
    channel = guild.channels[0]
    attach: discord.Attachment = discord.Attachment(
        state=dpytest.back.get_state(),
        data=dpytest.back.facts.make_attachment_dict(
            "test.jpg",
            15112122,
            "https://media.discordapp.net/attachments/some_number/random_number/test.jpg",
            "https://media.discordapp.net/attachments/some_number/random_number/test.jpg",
            height=1000,
            width=1000,
            content_type="image/jpeg"
        )
    )
    message_dict = dpytest.back.facts.make_message_dict(channel, author, attachments=[attach])
    try:
        message: discord.Message = discord.Message(state=dpytest.back.get_state(), channel=channel, data=message_dict)
    except Exception as err:
        pytest.fail(str(err))
