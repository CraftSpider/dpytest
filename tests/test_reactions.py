import pytest


@pytest.mark.asyncio
async def test_add_reaction(bot):
    g = bot.guilds[0]
    c = g.text_channels[0]

    message = await c.send("Test Message")
    await message.add_reaction("😂")

    # This is d.py/discord's fault, the message object from send isn't the same as the one in the state
    message = await c.fetch_message(message.id)
    assert len(message.reactions) == 1


@pytest.mark.asyncio
async def test_remove_reaction(bot):
    g = bot.guilds[0]
    c = g.text_channels[0]

    message = await c.send("Test Message")
    await message.add_reaction("😂")  # Assumes the test above passed
    await message.remove_reaction("😂", g.me)

    message = await c.fetch_message(message.id)
    assert len(message.reactions) == 0
