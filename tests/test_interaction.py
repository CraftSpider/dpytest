"""
    Tests for application command (slash command) interaction support.
"""

import pytest
import pytest_asyncio
import discord
import discord.ext.commands as commands
import discord.ext.test as dpytest
from typing import Callable, TypeVar
from discord import app_commands
from discord.client import _LoopSentinel

T = TypeVar('T')


@pytest_asyncio.fixture
async def bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    b = commands.Bot(command_prefix="!",
                     intents=intents)
    if isinstance(b.loop, _LoopSentinel):
        await b._async_setup_hook()

    @b.tree.command(name="ping", description="A simple ping command")
    async def ping(interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Pong!")

    @b.tree.command(name="greet", description="Greet someone")
    @app_commands.describe(name="The name to greet")
    async def greet(interaction: discord.Interaction, name: str) -> None:
        await interaction.response.send_message(f"Hello, {name}!")

    @b.tree.command(name="secret", description="Secret ephemeral command")
    async def secret(interaction: discord.Interaction) -> None:
        await interaction.response.send_message("This is secret!", ephemeral=True)

    @b.tree.command(name="embed_cmd", description="Send an embed")
    async def embed_cmd(interaction: discord.Interaction) -> None:
        embed = discord.Embed(title="Test Embed", description="Hello from embed!")
        await interaction.response.send_message(embed=embed)

    dpytest.configure(b)
    return b


@pytest.mark.asyncio
async def test_simple_interaction(bot: commands.Bot) -> None:
    """Test a basic slash command interaction."""
    await dpytest.interaction("ping")
    assert dpytest.verify().interaction().content("Pong!")


@pytest.mark.asyncio
async def test_interaction_with_option(bot: commands.Bot) -> None:
    """Test a slash command with options."""
    await dpytest.interaction(
        "greet",
        options=[{"name": "name", "type": 3, "value": "World"}],
    )
    assert dpytest.verify().interaction().content("Hello, World!")


@pytest.mark.asyncio
async def test_interaction_ephemeral(bot: commands.Bot) -> None:
    """Test an ephemeral slash command response."""
    await dpytest.interaction("secret")
    assert dpytest.verify().interaction().ephemeral()


@pytest.mark.asyncio
async def test_interaction_embed(bot: commands.Bot) -> None:
    """Test a slash command that sends an embed."""
    await dpytest.interaction("embed_cmd")
    expected_embed = discord.Embed(title="Test Embed", description="Hello from embed!")
    assert dpytest.verify().interaction().embed(expected_embed)


@pytest.mark.asyncio
async def test_interaction_nothing(bot: commands.Bot) -> None:
    """Test verify nothing when no interaction has been sent."""
    assert dpytest.verify().interaction().nothing()


@pytest.mark.asyncio
async def test_interaction_contains(bot: commands.Bot) -> None:
    """Test the contains modifier on interaction verification."""
    await dpytest.interaction("ping")
    assert dpytest.verify().interaction().contains().content("Pong")


@pytest.mark.asyncio
async def test_interaction_peek(bot: commands.Bot) -> None:
    """Test peeking at an interaction response without consuming it."""
    await dpytest.interaction("ping")
    assert dpytest.verify().interaction().peek().content("Pong!")
    # Should still be in the queue
    assert dpytest.verify().interaction().content("Pong!")


# --- Application owner / bot.application tests ---


class Unauthorized(app_commands.CheckFailure):
    def __init__(self, user: discord.User | discord.Member) -> None:
        self.user: discord.User | discord.Member = user
        super().__init__("You do not own this bot.")


def is_owner() -> Callable[[T], T]:
    def predicate(interaction: discord.Interaction) -> bool:
        if interaction.client.application is None:
            raise ValueError("This application is a lie")
        if interaction.user != interaction.client.application.owner:
            raise Unauthorized(interaction.user)
        return True
    return app_commands.check(predicate)


@pytest_asyncio.fixture
async def owner_bot() -> commands.Bot:
    """Bot fixture with an owner-only command."""
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    b = commands.Bot(command_prefix="!", intents=intents)
    if isinstance(b.loop, _LoopSentinel):
        await b._async_setup_hook()

    @b.tree.command(name="owneronly", description="Only the owner can use this")
    @is_owner()
    async def owneronly(interaction: discord.Interaction) -> None:
        await interaction.response.send_message("You are the owner!")

    @b.tree.command(name="public", description="Anyone can use this")
    async def public(interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Hello!")

    # Configure with 2 members; default owner=True makes member[0] the owner
    dpytest.configure(b, members=2)
    return b


@pytest.mark.asyncio
async def test_bot_application_not_none(owner_bot: commands.Bot) -> None:
    """bot.application should be populated after configure()."""
    assert owner_bot.application is not None
    assert owner_bot.application.owner is not None


@pytest.mark.asyncio
async def test_owner_default_is_first_member(owner_bot: commands.Bot) -> None:
    """With owner=True (default), the first test member is the app owner."""
    cfg = dpytest.get_config()
    assert owner_bot.application is not None
    assert owner_bot.application.owner.id == cfg.members[0].id


@pytest.mark.asyncio
async def test_owner_command_succeeds_for_owner(owner_bot: commands.Bot) -> None:
    """The owner can invoke an owner-only command."""
    await dpytest.interaction("owneronly", member=0)
    assert dpytest.verify().interaction().content("You are the owner!")


@pytest.mark.asyncio
async def test_owner_command_fails_for_non_owner(owner_bot: commands.Bot) -> None:
    """A non-owner invoking an owner-only command should trigger the check failure."""
    # member=1 is NOT the owner
    await dpytest.interaction("owneronly", member=1)
    # The check failure means no response is sent
    assert dpytest.verify().interaction().nothing()


@pytest.mark.asyncio
async def test_non_owner_can_use_public_command(owner_bot: commands.Bot) -> None:
    """A non-owner can still invoke commands without the owner check."""
    await dpytest.interaction("public", member=1)
    assert dpytest.verify().interaction().content("Hello!")


@pytest.mark.asyncio
async def test_interaction_member_param() -> None:
    """The member param on interaction() controls who sends the interaction."""
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    b = commands.Bot(command_prefix="!", intents=intents)
    if isinstance(b.loop, _LoopSentinel):
        await b._async_setup_hook()

    @b.tree.command(name="whoami", description="Tells you who you are")
    async def whoami(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"You are {interaction.user.name}")

    dpytest.configure(b, members=["Alice", "Bob"])
    cfg = dpytest.get_config()

    await dpytest.interaction("whoami", member=cfg.members[0])
    assert dpytest.verify().interaction().content(f"You are {cfg.members[0].name}")

    await dpytest.interaction("whoami", member=cfg.members[1])
    assert dpytest.verify().interaction().content(f"You are {cfg.members[1].name}")


@pytest.mark.asyncio
async def test_configure_explicit_owner() -> None:
    """Passing a specific user as owner= sets that user as the app owner."""
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    b = commands.Bot(command_prefix="!", intents=intents)
    if isinstance(b.loop, _LoopSentinel):
        await b._async_setup_hook()

    @b.tree.command(name="ping", description="Ping")
    async def ping(interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Pong!")

    dpytest.configure(b, members=["Alice", "Bob"], owner=False)
    cfg = dpytest.get_config()

    # With owner=False, the owner should be the default "TestOwner", not any test member
    assert b.application is not None
    assert b.application.owner.name != cfg.members[0].name
    assert b.application.owner.name != cfg.members[1].name


# --- Followup / defer / edit_original_response tests ---


@pytest_asyncio.fixture
async def followup_bot() -> commands.Bot:
    """Bot fixture with commands that use defer, followup, and edit_original_response."""
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    b = commands.Bot(command_prefix="!", intents=intents)
    if isinstance(b.loop, _LoopSentinel):
        await b._async_setup_hook()

    @b.tree.command(name="deferred", description="Defers then sends a followup")
    async def deferred(interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        await interaction.followup.send("Here is the result!")

    @b.tree.command(name="editoriginal", description="Responds then edits")
    async def editoriginal(interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Please wait...")
        await interaction.edit_original_response(content="Done!")

    @b.tree.command(name="deleteoriginal", description="Responds then deletes")
    async def deleteoriginal(interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Temporary")
        await interaction.delete_original_response()

    dpytest.configure(b)
    return b


@pytest.mark.asyncio
async def test_defer_then_followup(followup_bot: commands.Bot) -> None:
    """A command that defers then sends a followup should produce two responses."""
    await dpytest.interaction("deferred")

    # First response: the defer
    assert dpytest.verify().interaction().deferred()
    # Second response: the followup
    assert dpytest.verify().interaction().content("Here is the result!")


@pytest.mark.asyncio
async def test_edit_original_response(followup_bot: commands.Bot) -> None:
    """A command that sends then edits the original should produce two responses."""
    await dpytest.interaction("editoriginal")

    # First response: the initial message
    assert dpytest.verify().interaction().content("Please wait...")
    # Second response: the edit (response_type=7 = UPDATE_MESSAGE)
    assert dpytest.verify().interaction().content("Done!")


@pytest.mark.asyncio
async def test_delete_original_response(followup_bot: commands.Bot) -> None:
    """A command that sends then deletes the original should not crash."""
    await dpytest.interaction("deleteoriginal")

    # First response: the initial message
    assert dpytest.verify().interaction().content("Temporary")
    # The delete doesn't produce a queued response, so nothing else
    assert dpytest.verify().interaction().nothing()


# --- Unified queue behavior: all responses in one queue ---


@pytest_asyncio.fixture
async def dual_queue_bot() -> commands.Bot:
    """Bot fixture for testing that all responses go through the unified queue."""
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    b = commands.Bot(command_prefix="!", intents=intents)
    if isinstance(b.loop, _LoopSentinel):
        await b._async_setup_hook()

    @b.tree.command(name="public_reply", description="Non-ephemeral response")
    async def public_reply(interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Everyone can see this!")

    @b.tree.command(name="secret_reply", description="Ephemeral response")
    async def secret_reply(interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Only you can see this!", ephemeral=True)

    @b.tree.command(name="defer_public", description="Defers then sends public followup")
    async def defer_public(interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        await interaction.followup.send("Followup for everyone!")

    @b.tree.command(name="defer_ephemeral", description="Defers ephemerally then sends ephemeral followup")
    async def defer_ephemeral(interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Secret followup!", ephemeral=True)

    dpytest.configure(b)
    return b


@pytest.mark.asyncio
async def test_non_ephemeral_response_in_queue(dual_queue_bot: commands.Bot) -> None:
    """A non-ephemeral interaction response is in the unified queue."""
    await dpytest.interaction("public_reply")
    assert dpytest.verify().interaction().content("Everyone can see this!")


@pytest.mark.asyncio
async def test_ephemeral_response_in_queue(dual_queue_bot: commands.Bot) -> None:
    """An ephemeral interaction response is also in the unified queue."""
    await dpytest.interaction("secret_reply")
    assert dpytest.verify().interaction().ephemeral().content("Only you can see this!")


@pytest.mark.asyncio
async def test_nothing_after_ephemeral(dual_queue_bot: commands.Bot) -> None:
    """After consuming an ephemeral response, the queue is empty."""
    await dpytest.interaction("secret_reply")
    assert dpytest.verify().interaction().ephemeral().content("Only you can see this!")
    assert dpytest.verify().interaction().nothing()


@pytest.mark.asyncio
async def test_followup_non_ephemeral_ordering(dual_queue_bot: commands.Bot) -> None:
    """A defer + followup produces two items in the unified queue in order."""
    await dpytest.interaction("defer_public")

    # First: the defer
    assert dpytest.verify().interaction().deferred()
    # Second: the followup
    assert dpytest.verify().interaction().content("Followup for everyone!")


@pytest.mark.asyncio
async def test_followup_ephemeral_ordering(dual_queue_bot: commands.Bot) -> None:
    """An ephemeral defer + ephemeral followup produces two items in the unified queue."""
    await dpytest.interaction("defer_ephemeral")

    # First: the defer
    assert dpytest.verify().interaction().deferred()
    # Second: the ephemeral followup
    assert dpytest.verify().interaction().ephemeral().content("Secret followup!")
    # Queue is empty
    assert dpytest.verify().interaction().nothing()


@pytest.mark.asyncio
async def test_message_verify_fails_on_interaction_response(dual_queue_bot: commands.Bot) -> None:
    """verify().message() should fail when the front of the queue is an InteractionResponse."""
    await dpytest.interaction("public_reply")
    # The queue has an InteractionResponse, not a Message — so message verification fails
    assert not dpytest.verify().message().content("Everyone can see this!")
