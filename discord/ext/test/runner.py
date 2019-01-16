
import sys
import asyncio
import logging
import discord
import typing

from dpytest import backend as back


class RunnerConfig(typing.NamedTuple):
    client: discord.Client
    guilds: typing.List[discord.Guild]
    channels: typing.List[discord.abc.GuildChannel]
    members: typing.List[discord.Member]


log = logging.getLogger("discord.ext.tests")
_cur_config = None
sent_queue = asyncio.queues.Queue()
error_queue = asyncio.queues.Queue()


async def run_all_events():
    if sys.version_info[1] >= 7:
        pending = filter(lambda x: x._coro.__name__ == "_run_event", asyncio.all_tasks())
    else:
        pending = filter(lambda x: x._coro.__name__ == "_run_event", asyncio.Task.all_tasks())
    for task in pending:
        if not (task.done() or task.cancelled()):
            await task


def verify_message(text=None, equals=True):
    if text is None:
        equals = not equals
    try:
        message = sent_queue.get_nowait()
        if equals:
            assert message.content == text, f"Didn't find expected text. Expected {text}, found {message.content}"
        else:
            assert message.content != text, f"Found unexpected text. Expected something not matching {text}"
    except asyncio.QueueEmpty:
        raise AssertionError("No message returned by command")


def verify_embed(embed=None, allow_text=False, equals=True):
    if embed is None:
        equals = not equals
    try:
        message = sent_queue.get_nowait()
        if not allow_text:
            assert message.content is None

        emb = None
        if len(message.embeds) > 0:
            emb = message.embeds[0]
        if equals:
            assert emb == embed, "Didn't find expected embed"
        else:
            assert emb != embed, "Found unexpected embed"
    except asyncio.QueueEmpty:
        raise AssertionError("No message returned by command")


def verify_file(file=None, allow_text=False, equals=True):
    if file is None:
        equals = not equals
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


async def message(content, client=None, channel=0, member=0):
    if _cur_config is None:
        log.error("Attempted to make call before runner configured")
        return

    if client is None:
        client = _cur_config.client

    if isinstance(channel, int):
        channel = _cur_config.channels[channel]
    if isinstance(member, int):
        member = _cur_config.members[member]

    message = back.make_message(content, member, channel)

    client.dispatch("message", message)
    await run_all_events()

    if not error_queue.empty():
        err = await error_queue.get()
        raise err[1]


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
        if old_error:
            await old_error(ctx, error)
        await error_queue.put((ctx, error))

    on_command_error.__old__ = client.on_command_error
    client.on_command_error = on_command_error

    # Configure the factories module
    back.set_callback(message_callback, "message")

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
            user = back.make_user("TestUser", f"{num+1:04}")
            member = back.make_member(user, guild)
            members.append(member)
        back.make_member(back.get_state().user, guild)

    _cur_config = RunnerConfig(client, guilds, channels, members)
