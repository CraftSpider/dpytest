import discord
import pytest
import discord.ext.test as dpytest  # noqa: F401


@pytest.mark.asyncio
async def test_configure_guilds(bot: discord.Client) -> None:
    dpytest.configure(bot, guilds=2)
    assert len(bot.guilds) == 2
    assert bot.guilds[0].name == "Test Guild 0"
    assert bot.guilds[1].name == "Test Guild 1"

    dpytest.configure(bot, guilds=["Apples", "Bananas", "Oranges"])
    assert len(bot.guilds) == 3
    assert bot.guilds[0].name == "Apples"
    assert bot.guilds[1].name == "Bananas"
    assert bot.guilds[2].name == "Oranges"

    guild = bot.guilds[0]
    channel = guild.text_channels[0]
    await channel.send("Test Message")
    assert dpytest.verify().message().content("Test Message")


@pytest.mark.asyncio
async def test_configure_text_channels(bot: discord.Client) -> None:
    dpytest.configure(bot, text_channels=3)
    guild = bot.guilds[0]
    assert len(guild.text_channels) == 3
    for num, chan in enumerate(guild.text_channels):
        assert chan.name == f"TextChannel_{num}"

    dpytest.configure(bot, text_channels=["Fruits", "Videogames", "Coding", "Fun"])
    guild = bot.guilds[0]
    assert len(guild.text_channels) == 4
    assert guild.text_channels[0].name == "Fruits"
    assert guild.text_channels[1].name == "Videogames"
    assert guild.text_channels[2].name == "Coding"
    assert guild.text_channels[3].name == "Fun"

    # we can even use discord.utils.get
    channel = discord.utils.get(guild.text_channels, name='Videogames')
    assert channel is not None
    assert channel.name == "Videogames"
    await channel.send("Test Message")
    assert dpytest.verify().message().content("Test Message")


@pytest.mark.asyncio
async def test_configure_voice_channels(bot: discord.Client) -> None:
    dpytest.configure(bot, voice_channels=3)
    guild = bot.guilds[0]
    assert len(guild.voice_channels) == 3
    for num, chan in enumerate(guild.voice_channels):
        assert chan.name == f"VoiceChannel_{num}"

    dpytest.configure(bot, voice_channels=["Fruits", "Videogames", "Coding", "Fun"])
    guild = bot.guilds[0]
    assert len(guild.voice_channels) == 4
    assert guild.voice_channels[0].name == "Fruits"
    assert guild.voice_channels[1].name == "Videogames"
    assert guild.voice_channels[2].name == "Coding"
    assert guild.voice_channels[3].name == "Fun"

    # we can even use discord.utils.get
    channel = discord.utils.get(guild.voice_channels, name='Videogames')
    assert channel is not None
    assert channel.name == "Videogames"


@pytest.mark.asyncio
async def test_configure_members(bot: discord.Client) -> None:
    dpytest.configure(bot, members=3)
    guild = bot.guilds[0]
    assert len(guild.members) == 3 + 1  # because the bot is a member too
    for num, member in enumerate(guild.members[:3]):
        assert member.name == f"TestUser{str(num)}"

    dpytest.configure(bot, members=["Joe", "Jack", "William", "Averell"])
    guild = bot.guilds[0]
    assert len(guild.members) == 4 + 1  # because the bot is a member too
    assert guild.members[0].name == "Joe"
    assert guild.members[1].name == "Jack"
    assert guild.members[2].name == "William"
    assert guild.members[3].name == "Averell"

    # we can even use discord.utils.get
    william_member = discord.utils.get(guild.members, name='William')
    assert  william_member is not None
    assert william_member.name == "William"


@pytest.mark.asyncio
@pytest.mark.cogs("cogs.echo")
async def test_configure_all(bot: discord.Client) -> None:
    dpytest.configure(bot,
                      guilds=["CoolGuild", "LameGuild"],
                      text_channels=["Fruits", "Videogames"], voice_channels=["Apples", "Bananas"],
                      members=["Joe", "Jack", "William", "Averell"])
    guild = bot.guilds[1]
    channel = discord.utils.get(guild.text_channels, name='Videogames')
    assert channel is not None
    jack = discord.utils.get(guild.members, name="Jack")
    assert jack is not None
    mess = await dpytest.message("!echo Hello, my name is Jack", channel=channel, member=jack)
    assert mess.author.name == "Jack"
    assert mess.channel.name == "Videogames"  # type: ignore[union-attr]
    assert dpytest.verify().message().content("Hello, my name is Jack")
