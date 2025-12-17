import discord
import pytest
import discord.ext.test as dpytest


@pytest.mark.asyncio
async def test_messasge(bot: discord.Client) -> None:
    """Test make_message_dict from factory.
    """
    guild = bot.guilds[0]
    author: discord.Member = guild.members[0]
    channel: discord.TextChannel = guild.channels[0]  # type: ignore[assignment]
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
        message: discord.Message = discord.Message(state=dpytest.back.get_state(), channel=channel, data=message_dict)  # noqa: E501,F841 (variable never used)
    except Exception as err:
        pytest.fail(str(err))
