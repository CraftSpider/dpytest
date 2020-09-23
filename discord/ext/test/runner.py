"""
    Main module for setting up and running tests using dpytest.
    Handles configuration of a bot, and setup of the discord environment
"""


import sys
import asyncio
import logging
import discord
import typing

from . import backend as back, callbacks
from .utils import embed_eq


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
sent_queue = asyncio.queues.Queue()
error_queue = asyncio.queues.Queue()


def require_config(func):
    def wrapper(*args, **kwargs):
        if _cur_config is None:
            log.error("Attempted to make call before runner configured")
            raise RuntimeError(f"Configure runner before calling {func.__name__}")
        return func(*args, **kwargs)
    wrapper.__wrapped__ = func
    return wrapper


async def run_all_events():
    """
        Ensure that all dpy related coroutines have completed or been cancelled
    """
    while True:
        if sys.version_info[1] >= 7:
            pending = asyncio.all_tasks()
        else:
            pending = asyncio.Task.all_tasks()
        if not any(map(lambda x: x._coro.__name__ == "_run_event" and not (x.done() or x.cancelled()) , pending)):
            break
        for task in pending:
            if task._coro.__name__ == "_run_event" and not (task.done() or task.cancelled()):
                await task



async def finish_on_command_error():
    """
        Ensure that all dpy related coroutines have completed or been cancelled
    """
    if sys.version_info[1] >= 7:
        pending = filter(lambda x: x._coro.__name__ == "_run_event", asyncio.all_tasks())
    else:
        pending = filter(lambda x: x._coro.__name__ == "_run_event", asyncio.Task.all_tasks())
    for task in pending:
        if not (task.done() or task.cancelled()):
            await task


def verify_message(text=None, equals=True, contains=False, peek=False, assert_nothing=False):
    """
        Assert that a message was sent with the given text, or that a message was sent that *doesn't* match the
        given text

    :param text: Text to match, or None to match anything
    :param equals: Whether to negate the check
    :param assert_nothing: Whether to assert that nothing was sent at all
    """
    if text is None:
        equals = not equals
    if assert_nothing:
        assert sent_queue.qsize() == 0, f"A message was not meant to be sent but this message was sent {sent_queue.get_nowait().content}"
        return

    try:
        message = sent_queue.get_nowait()
        if peek:
            messages = [message]
            while not sent_queue.empty():
                tmp_message = sent_queue.get_nowait()
                messages.append(tmp_message)
            for tmp_message in messages:
                sent_queue.put_nowait(tmp_message)
        if equals:
            if contains:
                assert text in message.content,f"Didn't find expected text. Expected {text} to be in {message.content}"
            else:
                assert message.content == text, f"Didn't find expected text. Expected {text}, found {message.content}"
        else:
            if contains:
                assert text not in message.content, f"Found unexpected text. Expected something not containing {text}"
            else:
                assert message.content != text, f"Found unexpected text. Expected something not matching {text}"
    except asyncio.QueueEmpty:
        raise AssertionError("No message returned by command")

def get_message(peek=False):
    """
        Allow the user to retrieve a message sent by the bot

    :param peek: do not remove the message from the queue of messages
    :return:
    """
    message = sent_queue.get_nowait()
    if peek:
        messages = [message]
        while not sent_queue.empty():
            tmp_message = sent_queue.get_nowait()
            messages.append(tmp_message)
        for tmp_message in messages:
            sent_queue.put_nowait(tmp_message)
    return message

def verify_embed(embed=None, allow_text=False, equals=True, peek=False,assert_nothing=False):
    """
        Assert that a message was sent containing an embed, or that a message was sent not
        containing an embed

    :param embed: Embed to compare against
    :param allow_text: Whether non-embed text is allowed
    :param equals: Whether to invert the assertion
    :param assert_nothing: Whether to assert that no message was sent
    """
    if embed is None:
        equals = not equals
    if assert_nothing:
        assert sent_queue.qsize() == 0, f"A message was not meant to be sent but this message was sent {sent_queue.get_nowait().content}"
        return

    try:
        message = sent_queue.get_nowait()
        if not allow_text:
            assert message.content is None
        if peek:
            messages = [message]
            while not sent_queue.empty():
                tmp_message = sent_queue.get_nowait()
                messages.append(tmp_message)
            for tmp_message in messages:
                sent_queue.put_nowait(tmp_message)
        emb = None
        if len(message.embeds) > 0:
            emb = message.embeds[0]
        if equals:
            assert embed_eq(emb, embed), "Didn't find expected embed"
        else:
            assert not embed_eq(emb, embed), "Found unexpected embed"
    except asyncio.QueueEmpty:
        raise AssertionError("No message returned by command")

def get_embed(peek=False):
    """
        Allow the user to retrieve an embed in a message sent by the bot

    :param peek: do not remove the message from the queue of messages
    :return:
    """
    message = sent_queue.get_nowait()
    if peek:
        messages = [message]
        while not sent_queue.empty():
            tmp_message = sent_queue.get_nowait()
            messages.insert(0,tmp_message)
        for tmp_message in messages:
            sent_queue.put_nowait(tmp_message)
    return message.embeds[0]


def verify_file(file=None, allow_text=False, equals=True, assert_nothing=False):
    if file is None:
        equals = not equals
    if assert_nothing:
        assert sent_queue.qsize() == 0, f"A message was not meant to be sent but this message was sent {sent_queue.get_nowait().content}"

    try:
        message = sent_queue.get_nowait()
        if not allow_text:
            assert message.content is None

        attach = None
        if len(message.attachments) > 0:
            attach = message.attachments[0]
        if equals:
            assert attach == file, "Didn't find expected file"
        else:
            assert attach != file, "Found unexpected file"
    except asyncio.QueueEmpty:
        raise AssertionError("No message returned by command")


def verify_activity(activity=None, equals=True):
    if activity is None:
        equals = not equals
    me = _cur_config.guilds[0].me

    me_act = me.activity
    if isinstance(activity, discord.Activity):
        activity = (activity.name, activity.url, activity.type)
    if isinstance(me_act, discord.Activity):
        me_act = (me_act.name, me_act.url, me_act.type)

    if equals:
        assert me_act == activity, "Didn't find expected activity"
    else:
        assert me_act != activity, "Found unexpected activity"


async def empty_queue():
    await run_all_events()
    while not sent_queue.empty():
        await sent_queue.get()
    while not error_queue.empty():
        await error_queue.get()


async def message_callback(message):
    await sent_queue.put(message)


async def error_callback(ctx, error):
    await error_queue.put((ctx, error))


async def create_role_callback(guild, role, reason=None):
    roles = [role] + guild.roles
    if role.position == -1:
        for r in roles:
            if r.position != 0:
                r.position += 1
        role.position = 1
    back.update_guild(guild, roles=roles)


async def move_role_callback(guild, role, positions, reason=None):
    for pair in positions:
        guild._roles[pair["id"]].position = pair["position"]


async def add_role_callback(member, role, reason=None):
    roles = [role] + [x for x in member.roles if x.id != member.guild.id]
    back.update_member(member, roles=roles)


async def remove_role_callback(member, role, reason=None):
    roles = [x for x in member.roles if x != role and x.id != member.guild.id]
    back.update_member(member, roles=roles)


@require_config
async def message(content, channel=0, member=0):
    if isinstance(channel, int):
        channel = _cur_config.channels[channel]
    if isinstance(member, int):
        member = _cur_config.members[member]

    mes = back.make_message(content, member, channel)

    await run_all_events()


    if not error_queue.empty():
        err = await error_queue.get()
        raise err[1]

    return mes


@require_config
async def set_permission_overrides(target, channel, overrides=None, **kwars):
    if kwars:
        if overrides:
            raise ValueError("either overrides parameter or kwargs")
        else:
            overrides = discord.PermissionOverwrite(**kwars)

    if isinstance(target, int):
        target = _cur_config.members[target]
    if isinstance(channel, int):
        channel = _cur_config.channels[channel]

    if not isinstance(channel, discord.abc.GuildChannel):
        raise TypeError(f"channel '{channel}' must be a abc.GuildChannel, not '{type(channel)}''")
    if not isinstance(target, (discord.abc.User, discord.Role)):
        raise TypeError(f"target '{target}' must be a abc.User or Role, not '{type(target)}''")

    back.update_text_channel(channel, target, overrides)


@require_config
async def add_role(member, role):
    if isinstance(member, int):
        member = _cur_config.members[member]
    if not isinstance(role, discord.Role):
        raise TypeError("Role argument must be of type discord.Role")

    roles = [role] + [x for x in member.roles if x.id != member.guild.id]
    back.update_member(member, roles=roles)


@require_config
async def remove_role(member, role):
    if isinstance(member, int):
        member = _cur_config.members[member]
    if not isinstance(role, discord.Role):
        raise TypeError("Role argument must be of type discord.Role")

    roles = [x for x in member.roles if x.id != role.id and x.id != member.guild.id]
    back.update_member(member, roles=roles)


@require_config
async def member_join(guild=0, user=None, *, name=None, discrim=None):
    import random
    if isinstance(guild, int):
        guild = _cur_config.guilds[guild]

    if user is None:
        if name is None:
            name = "TestUser"
        if discrim is None:
            discrim = random.randint(1, 9999)
        user = back.make_user("TestUser", discrim)
    member = back.make_member(user, guild)
    return member


def get_config():
    return _cur_config


def configure(client, num_guilds=1, num_channels=1, num_members=1):
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
    callbacks.set_callback(message_callback, "send_message")
    callbacks.set_callback(create_role_callback, "create_role")
    callbacks.set_callback(move_role_callback, "move_role")
    callbacks.set_callback(add_role_callback, "add_role")
    callbacks.set_callback(remove_role_callback, "remove_role")

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
        back.make_member(back.get_state().user, guild)

    back.get_state().start_dispatch()

    _cur_config = RunnerConfig(client, guilds, channels, members)
