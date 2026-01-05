"""
    Main module for setting up and running tests using dpytest.
    Handles configuration of a bot, and setup of the discord environment.

    All public functions in this module are re-exported at ``discord.ext.test``, this is the primary
    entry point for users of the library and most of what they should interact with

    See also:
        :mod:`discord.ext.test.verify`
"""

import sys
import asyncio
import logging
from typing import NamedTuple, Callable, Any

import discord
import pathlib

from itertools import count

from discord.ext import commands
from discord.ext.commands import CommandError
from discord.ext.commands._types import BotT
from typing_extensions import ParamSpec, TypeVar

from . import backend as back, callbacks, _types
from .callbacks import CallbackEvent
from .utils import PeekableQueue


class RunnerConfig(NamedTuple):
    """
        Exposed discord test configuration
        Contains the current client, and lists of faked objects
    """

    client: discord.Client
    guilds: list[discord.Guild]
    channels: list[discord.abc.GuildChannel]
    members: list[discord.Member]


log = logging.getLogger("discord.ext.tests")
_cur_config: RunnerConfig | None = None
sent_queue: PeekableQueue[discord.Message] = PeekableQueue()
error_queue: PeekableQueue[tuple[
    commands.Context[commands.Bot | commands.AutoShardedBot], CommandError
]] = PeekableQueue()


T = TypeVar('T')
P = ParamSpec('P')


def require_config(func: Callable[P, T]) -> Callable[P, T]:
    """
        Decorator to enforce that configuration is completed before the decorated function is
        called.

    :param func: Function to decorate
    :return: Function with added check for configuration being setup
    """

    wrapper: _types.Wrapper[P, T]

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:  # type: ignore[no-redef]
        if _cur_config is None:
            log.error("Attempted to make call before runner configured")
            raise RuntimeError(f"Configure runner before calling {func.__name__}")
        return func(*args, **kwargs)

    wrapper.__wrapped__ = func
    wrapper.__annotations__ = func.__annotations__
    wrapper.__doc__ = func.__doc__
    return wrapper


def _task_coro_name(task: asyncio.Task[Any]) -> str | None:
    """
        Uses getattr() to avoid AttributeErrors when the coroutine doesn't have a __name__
    """
    return getattr(task.get_coro(), "__name__", None)


async def run_all_events() -> None:
    """
        Ensure that all dpy related coroutines have completed or been cancelled. If any dpy coroutines
        are currently running, this will also wait for those.
    """
    while True:
        if sys.version_info[1] >= 7:
            pending = asyncio.all_tasks()
        else:
            pending = asyncio.Task.all_tasks()
        if not any(map(lambda x: _task_coro_name(x) == "_run_event" and not (x.done() or x.cancelled()), pending)):
            break
        for task in pending:
            if _task_coro_name(task) == "_run_event" and not (task.done() or task.cancelled()):
                await task


async def finish_on_command_error() -> None:
    """
        Ensure that all dpy related coroutines have completed or been cancelled. This will only
        wait for dpy related coroutines, not any other coroutines currently running.
    """
    if sys.version_info[1] >= 7:
        pending = filter(lambda x: _task_coro_name(x) == "_run_event", asyncio.all_tasks())
    else:
        pending = filter(lambda x: _task_coro_name(x) == "_run_event", asyncio.Task.all_tasks())
    for task in pending:
        if not (task.done() or task.cancelled()):
            await task


def get_message(peek: bool = False) -> discord.Message:
    """
        Allow the user to retrieve the most recent message sent by the bot

    :param peek: If true, message will not be removed from the queue
    :return: Most recent message from the queue
    """
    if peek:
        message = sent_queue.peek()
    else:
        message = sent_queue.get_nowait()
    return message


def get_embed(peek: bool = False) -> discord.Embed:
    """
        Allow the user to retrieve an embed in a message sent by the bot

    :param peek: do not remove the message from the queue of messages
    :return: Embed of the most recent message in the queue
    """

    if peek:
        message = sent_queue.peek()
    else:
        message = sent_queue.get_nowait()
    return message.embeds[0]


async def empty_queue() -> None:
    """
        Empty the current message queue. Waits for all events to complete to ensure queue
        is not immediately added to after running.
    """
    await run_all_events()
    while not sent_queue.empty():
        await sent_queue.get()
    while not error_queue.empty():
        await error_queue.get()


async def _message_callback(message: discord.Message) -> None:
    """
        Internal callback, on a message being sent (in any channel) adds it to the queue

    :param message: Message sent on discord
    """
    await sent_queue.put(message)


async def _edit_member_callback(fields: Any, member: discord.Member, reason: str | None) -> None:
    """
        Internal callback. Updates a guild's voice states to reflect the given Member connecting to the given channel.
        Other updates to members are handled in http.edit_member().

    :param fields: Fields passed in from Member.edit().
    :param member: The Member to edit.
    :param reason: The reason for editing. Not used.
    """
    data = {'user_id': member.id}
    guild = member.guild
    channel = fields.get('channel_id')
    if not fields.get('nick') and not fields.get('roles'):
        # Data is allowed to not contain fields
        guild._update_voice_state(data, channel)  # type: ignore[arg-type]


counter = count(0)


@require_config
async def message(
        content: str,
        channel: _types.AnyChannel | int = 0,
        member: discord.Member | int = 0,
        attachments: list[pathlib.Path | str] | None = None
) -> discord.Message:
    """
        Fake a message being sent by some user to a channel.

    :param content: Content of the message
    :param channel: Channel to send to, or index into the config list
    :param member: Member sending the message, or index into the config list
    :param attachments: Message attachments to include, as file paths.
    :return: New message that was sent
    """
    if isinstance(channel, int):
        channel = get_config().channels[channel]
    if isinstance(member, int):
        member = get_config().members[member]
    import os
    if attachments is None:
        attachments = []
    attachments_model = [
        discord.Attachment(
            data={
                'id': counter.__next__(),
                'filename': os.path.basename(attachment),
                'size': 0,
                'url': str(attachment),
                'proxy_url': "",
                'height': 0,
                'width': 0
            },
            state=back.get_state()
        ) for attachment in attachments
    ]

    mes = back.make_message(content, member, channel, attachments=attachments_model)

    await run_all_events()

    if not error_queue.empty():
        err = await error_queue.get()
        raise err[1]

    return mes


@require_config
async def set_permission_overrides(
        target: discord.Member | discord.Role | int,
        channel: discord.abc.GuildChannel | int,
        overrides: discord.PermissionOverwrite | None = None,
        **kwargs: Any,
) -> None:
    """
        Set the permission override for a channel, as if set by another user.

    :param target: User or Role the permissions override is being set for
    :param channel: Channel the permissions are being set on
    :param overrides: The permissions to use, as an object. Conflicts with using ``kwargs``
    :param kwargs: The permissions to use, as a set of keys and values. Conflicts with using ``overrides``
    """
    if kwargs:
        if overrides:
            raise ValueError("Must supply either overrides parameter or kwargs, not both")
        else:
            overrides = discord.PermissionOverwrite(**kwargs)

    if isinstance(target, int):
        target = get_config().members[target]
    if isinstance(channel, int):
        channel = get_config().channels[channel]

    if not isinstance(channel, discord.TextChannel):
        raise TypeError(f"channel '{channel}' must be a discord.TextChannel, not '{type(channel)}''")
    if not isinstance(target, (discord.abc.User, discord.Role)):
        raise TypeError(f"target '{target}' must be an abc.User or Role, not '{type(target)}''")

    # TODO: This will probably break for video channels/non-standard text channels
    back.update_text_channel(channel, target, overrides)


@require_config
async def add_role(member: discord.Member | int, role: discord.Role) -> None:
    """
        Add a role to a member, as if added by another user.

    :param member: Member to add the role to
    :param role: Role to be added
    """
    if isinstance(member, int):
        member = get_config().members[member]
    if not isinstance(role, discord.Role):
        raise TypeError("Role argument must be of type discord.Role")

    roles = [role] + [x for x in member.roles if x.id != member.guild.id]
    back.update_member(member, roles=roles)


@require_config
async def remove_role(member: discord.Member | int, role: discord.Role) -> None:
    """
        Remove a role from a member, as if removed by another user.

    :param member: Member to remove the role from
    :param role: Role to remove
    """
    if isinstance(member, int):
        member = get_config().members[member]
    if not isinstance(role, discord.Role):
        raise TypeError("Role argument must be of type discord.Role")

    roles = [x for x in member.roles if x.id != role.id and x.id != member.guild.id]
    back.update_member(member, roles=roles)


@require_config
async def add_reaction(user: discord.user.BaseUser | discord.abc.User,
                       message: discord.Message, emoji: str) -> None:
    """
        Add a reaction to a message, as if added by another user

    :param user: User who reacted
    :param message: Message they reacted to
    :param emoji: Emoji that was used
    """
    back.add_reaction(message, user, emoji)
    await run_all_events()


@require_config
async def remove_reaction(user: discord.user.BaseUser | discord.Member,
                          message: discord.Message, emoji: str) -> None:
    """
        Remove a reaction from a message, as if done by another user

    :param user: User who removed their react
    :param message: Message they removed react from
    :param emoji: Emoji that was removed
    """
    back.remove_reaction(message, user, emoji)
    await run_all_events()


@require_config
async def member_join(
        guild: discord.Guild | int = 0,
        user: discord.User | None = None,
        *,
        name: str | None = None,
        discrim: str | int | None = None
) -> discord.Member:
    """
        Have a new member join a guild, either an existing or new user for the framework

    :param guild: Guild member is joining
    :param user: User to join, or None to create a new user
    :param name: If creating a new user, the name of the user. None to auto-generate
    :param discrim: If creating a new user, the discrim of the user. None to auto-generate
    """
    import random
    if isinstance(guild, int):
        guild = _cur_config.guilds[guild]  # type: ignore[union-attr]

    if user is None:
        if name is None:
            name = "TestUser"
        if discrim is None:
            discrim = random.randint(1, 9999)
        user = back.make_user(name, discrim)
    elif name is not None or discrim is not None:
        raise ValueError("Cannot supply user at the same time as name/discrim")
    member = back.make_member(user, guild)
    return member


def get_config() -> RunnerConfig:
    """
        Get the current runner configuration

    :return: Current runner config
    """
    if _cur_config is None:
        raise RuntimeError("Runner not configured yet")
    return _cur_config


def configure(client: discord.Client,
              guilds: int | list[str] = 1,
              text_channels: int | list[str] = 1,
              voice_channels: int | list[str] = 1,
              members: int | list[str] = 1) -> None:
    """
        Set up the runner configuration. This should be done before any tests are run.

    :param client: Client to configure with. Should be the bot/client that is going to be tested.
    :param guilds: Number or list of names of guilds to start the configuration with. Default is 1
    :param text_channels: Number or list of names of text channels in each guild to start with. Default is 1
    :param voice_channels: Number or list of names of voice channels in each guild to start with. Default is 1.
    :param members: Number or list of names of members in each guild (other than the client) to start with. Default is 1.
    """  # noqa: E501

    global _cur_config

    if not isinstance(client, discord.Client):
        raise TypeError("Runner client must be an instance of discord.Client")
    if isinstance(client, discord.AutoShardedClient):
        raise TypeError("Sharded clients not yet supported")

    back.configure(client)

    # Wrap on_error so errors will be reported
    old_error = None
    if hasattr(client, "on_command_error"):
        old_error = client.on_command_error

    on_command_error: _types.FnWithOld[[commands.Context[commands.Bot | commands.AutoShardedBot], CommandError], None]

    async def on_command_error(ctx: commands.Context[BotT], error: CommandError) -> None:  # type: ignore[no-redef]
        try:
            if old_error:
                await old_error(ctx, error)
        finally:
            await error_queue.put((ctx, error))

    on_command_error.__old__ = old_error

    client.on_command_error = on_command_error  # type: ignore[attr-defined]

    # Configure global callbacks
    callbacks.set_callback(_message_callback, CallbackEvent.send_message)
    callbacks.set_callback(_edit_member_callback, CallbackEvent.edit_member)

    back.get_state().stop_dispatch()

    _guilds = []
    if isinstance(guilds, int):
        for num in range(guilds):
            guild = back.make_guild(f"Test Guild {num}")
            _guilds.append(guild)
    if isinstance(guilds, list):
        for guild_name in guilds:
            guild = back.make_guild(guild_name)
            _guilds.append(guild)

    _channels: list[discord.abc.GuildChannel] = []
    _members = []
    for guild in _guilds:
        # Text channels
        if isinstance(text_channels, int):
            for num in range(text_channels):
                text = back.make_text_channel(f"TextChannel_{num}", guild)
                _channels.append(text)
        if isinstance(text_channels, list):
            for chan in text_channels:
                text = back.make_text_channel(chan, guild)
                _channels.append(text)

        # Voice channels
        if isinstance(voice_channels, int):
            for num in range(voice_channels):
                voice = back.make_voice_channel(f"VoiceChannel_{num}", guild)
                _channels.append(voice)
        if isinstance(voice_channels, list):
            for chan in voice_channels:
                voice = back.make_voice_channel(chan, guild)
                _channels.append(voice)

        # Members
        if isinstance(members, int):
            for num in range(members):
                user = back.make_user(f"TestUser{str(num)}", f"{num + 1:04}")
                member = back.make_member(user, guild, nick=f"{user.name}_{str(num)}_nick")
                _members.append(member)
        if isinstance(members, list):
            for num, name in enumerate(members):
                user = back.make_user(name, f"{num + 1:04}")
                member = back.make_member(user, guild, nick=f"{user.name}_{str(num)}_nick")
                _members.append(member)

        client_user = back.get_state().user
        if client_user is not None:
            back.make_member(client_user, guild, nick=f"{client_user.name}_nick")

    back.get_state().start_dispatch()

    _cur_config = RunnerConfig(client, _guilds, _channels, _members)
