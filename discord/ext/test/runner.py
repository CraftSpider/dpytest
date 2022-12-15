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
import discord
import typing
import pathlib

from itertools import count

from . import backend as back, callbacks, _types
from .utils import PeekableQueue


class RunnerConfig(typing.NamedTuple):
    """
        Exposed discord test configuration
        Contains the current client, and lists of faked objects
    """

    client: discord.Client
    guilds: typing.List[discord.Guild]
    channels: typing.List[discord.abc.GuildChannel]
    members: typing.List[discord.Member]


log = logging.getLogger("discord.ext.tests")
_cur_config: typing.Optional[RunnerConfig] = None
sent_queue: PeekableQueue = PeekableQueue()
error_queue: PeekableQueue = PeekableQueue()


def require_config(func: typing.Callable[..., _types.T]) -> typing.Callable[..., _types.T]:
    """
        Decorator to enforce that configuration is completed before the decorated function is
        called.

    :param func: Function to decorate
    :return: Function with added check for configuration being setup
    """
    def wrapper(*args, **kwargs):
        if _cur_config is None:
            log.error("Attempted to make call before runner configured")
            raise RuntimeError(f"Configure runner before calling {func.__name__}")
        return func(*args, **kwargs)
    wrapper.__wrapped__ = func
    wrapper.__annotations__ = func.__annotations__
    wrapper.__doc__ = func.__doc__
    return wrapper


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
        if not any(map(lambda x: x._coro.__name__ == "_run_event" and not (x.done() or x.cancelled()), pending)):
            break
        for task in pending:
            if task._coro.__name__ == "_run_event" and not (task.done() or task.cancelled()):
                await task


async def finish_on_command_error() -> None:
    """
        Ensure that all dpy related coroutines have completed or been cancelled. This will only
        wait for dpy related coroutines, not any other coroutines currently running.
    """
    if sys.version_info[1] >= 7:
        pending = filter(lambda x: x._coro.__name__ == "_run_event", asyncio.all_tasks())
    else:
        pending = filter(lambda x: x._coro.__name__ == "_run_event", asyncio.Task.all_tasks())
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


counter = count(0)


@require_config
async def message(
        content: str,
        channel: typing.Union[_types.AnyChannel, int] = 0,
        member: typing.Union[discord.Member, int] = 0,
        attachments: typing.List[typing.Union[pathlib.Path, str]] = None
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
        channel = _cur_config.channels[channel]
    if isinstance(member, int):
        member = _cur_config.members[member]
    import os
    if attachments is None:
        attachments = []
    attachments = [
        discord.Attachment(
            data={
                'id': counter.__next__(),
                'filename': os.path.basename(attachment),
                'size': 0,
                'url': attachment,
                'proxy_url': "",
                'height': 0,
                'width': 0
            },
            state=back.get_state()
        ) for attachment in attachments
    ]

    mes = back.make_message(content, member, channel, attachments=attachments)

    await run_all_events()

    if not error_queue.empty():
        err = await error_queue.get()
        raise err[1]

    return mes


@require_config
async def set_permission_overrides(
        target: typing.Union[discord.User, discord.Role],
        channel: discord.abc.GuildChannel,
        overrides: typing.Optional[discord.PermissionOverwrite] = None,
        **kwargs: typing.Any,
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
        target = _cur_config.members[target]
    if isinstance(channel, int):
        channel = _cur_config.channels[channel]

    if not isinstance(channel, discord.abc.GuildChannel):
        raise TypeError(f"channel '{channel}' must be a abc.GuildChannel, not '{type(channel)}''")
    if not isinstance(target, (discord.abc.User, discord.Role)):
        raise TypeError(f"target '{target}' must be a abc.User or Role, not '{type(target)}''")

    # TODO: This will probably break for video channels/non-standard text channels
    back.update_text_channel(channel, target, overrides)


@require_config
async def add_role(member: discord.Member, role: discord.Role) -> None:
    """
        Add a role to a member, as if added by another user.

    :param member: Member to add the role to
    :param role: Role to be added
    """
    if isinstance(member, int):
        member = _cur_config.members[member]
    if not isinstance(role, discord.Role):
        raise TypeError("Role argument must be of type discord.Role")

    roles = [role] + [x for x in member.roles if x.id != member.guild.id]
    back.update_member(member, roles=roles)


@require_config
async def remove_role(member: discord.Member, role: discord.Role) -> None:
    """
        Remove a role from a member, as if removed by another user.

    :param member: Member to remove the role from
    :param role: Role to remove
    """
    if isinstance(member, int):
        member = _cur_config.members[member]
    if not isinstance(role, discord.Role):
        raise TypeError("Role argument must be of type discord.Role")

    roles = [x for x in member.roles if x.id != role.id and x.id != member.guild.id]
    back.update_member(member, roles=roles)


@require_config
async def add_reaction(
    user: typing.Union[discord.user.BaseUser, discord.abc.User], message: discord.Message, emoji: str
) -> None:
    """
        Add a reaction to a message, as if added by another user

    :param user: User who reacted
    :param message: Message they reacted to
    :param emoji: Emoji that was used
    """
    back.add_reaction(message, user, emoji)
    await run_all_events()


@require_config
async def remove_reaction(
    user: typing.Union[discord.user.BaseUser, discord.abc.User], message: discord.Message, emoji: str
) -> None:
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
        guild: typing.Union[discord.Guild, int] = 0,
        user: typing.Optional[discord.User] = None,
        *,
        name: str = None,
        discrim: typing.Union[str, int] = None
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
        guild = _cur_config.guilds[guild]

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
    return _cur_config


def configure(client: discord.Client, num_guilds: int = 1, num_channels: int = 1, num_members: int = 1) -> None:
    """
        Set up the runner configuration. This should be done before any tests are run.

    :param client: Client to configure with. Should be the bot/client that is going to be tested.
    :param num_guilds: Number of guilds to start the configuration with. Default is 1
    :param num_channels: Number of text channels in each guild to start with. Default is 1
    :param num_members: Number of members in each guild (other than the client) to start with. Default is 1.
    """

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

    async def on_command_error(ctx, error):
        try:
            if old_error:
                await old_error(ctx, error)
        finally:
            await error_queue.put((ctx, error))

    on_command_error.__old__ = old_error
    client.on_command_error = on_command_error

    # Configure global callbacks
    callbacks.set_callback(_message_callback, "send_message")

    back.get_state().stop_dispatch()

    guilds = []
    for num in range(num_guilds):
        guild = back.make_guild(f"Test Guild {num}")
        guilds.append(guild)

    channels = []
    members = []
    for guild in guilds:
        for num in range(num_channels):
            channel = back.make_text_channel(f"Channel_{num}", guild)
            channels.append(channel)
        for num in range(num_members):
            user = back.make_user(f"TestUser{str(num)}", f"{num+1:04}")
            member = back.make_member(user, guild, nick=user.name + f"_{str(num)}_nick")
            members.append(member)
        back.make_member(back.get_state().user, guild, nick=client.user.name + "_nick")

    back.get_state().start_dispatch()

    _cur_config = RunnerConfig(client, guilds, channels, members)
