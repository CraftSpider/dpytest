"""
    Functions and classes for building various discord.py classes
"""

import asyncio
import sys
import logging
import typing
import pathlib
import discord
import discord.state as state
import discord.http as dhttp
import discord.gateway as gate

from dpytest import factories as facts


class BackendConfig(typing.NamedTuple):
    callbacks: typing.Dict[str, typing.Callable[[typing.Any], typing.Coroutine]]
    state: "FakeState"


log = logging.getLogger("discord.ext.tests")
_cur_config = None


class FakeHttp(dhttp.HTTPClient):

    fileno = 0

    def __init__(self, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()

        self.state = None

        super().__init__(connector=None, loop=loop)

    def _get_higher_locs(self, num):
        frame = sys._getframe(num + 1)
        locs = frame.f_locals
        del frame
        return locs

    async def request(self, *args, **kwargs):
        raise NotImplementedError("Operation occured that isn't captured by the tests framework")

    async def send_files(self, channel_id, *, files, content=None, tts=False, embed=None, nonce=None):
        locs = self._get_higher_locs(1)
        channel = locs.get("channel", None)

        attachments = []
        for file, name in files:
            path = pathlib.Path(f"./temp_{self.fileno}.dat")
            self.fileno += 1
            if file.seekable():
                file.seek(0)
            with open(path, "wb") as nfile:
                nfile.write(file.read())
            attachments.append((path, name))
        attachments = list(map(lambda x: make_attachment(*x), attachments))

        embeds = []
        if embed:
            embeds = [discord.Embed.from_data(embed)]
        data = facts.make_message_dict(channel, self.state.user, attachments=attachments, content=content, tts=tts,
                                       embeds=embeds, nonce=nonce)

        message = self.state.create_message(channel=channel, data=data)
        await _dispatch_event("message", message)

        return data

    async def send_message(self, channel_id, content, *, tts=False, embed=None, nonce=None):
        locs = self._get_higher_locs(1)
        channel = locs.get("channel", None)

        embeds = []
        if embed:
            embeds = [discord.Embed.from_data(embed)]
        data = facts.make_message_dict(channel, self.state.user, content=content, tts=tts, embeds=embeds, nonce=nonce)

        message = self.state.create_message(channel=channel, data=data)
        await _dispatch_event("message", message)

        return data

    async def application_info(self):
        # TODO: make these values configurable
        user = self.state.user
        data = {
            "id": user.id,
            "name": user.name,
            "icon": user.avatar,
            "description": "A test discord application",
            "rpc_origins": None,
            "bot_public": True,
            "bot_require_code_grant": False,
            "owner": facts.make_user_dict("TestOwner", "0001", None)
        }

        copy = data.copy()
        copy["owner"] = discord.User(state=get_state(), data=data["owner"])
        appinfo = discord.AppInfo(**copy)
        await _dispatch_event("info", appinfo)

        return data

    async def change_my_nickname(self, guild_id, nickname, *, reason=None):
        locs = self._get_higher_locs(1)
        me = locs.get("self", None)

        await _dispatch_event("nickname", nickname, me, reason=reason)

        return {"nick": nickname}

    async def edit_member(self, guild_id, user_id, *, reason=None, **fields):
        locs = self._get_higher_locs(1)
        member = locs.get("self", None)

        await _dispatch_event("edit", fields, member, reason=reason)

        print(fields)


class FakeWebSocket(gate.DiscordWebSocket):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cur_event = ""
        self.event_args = ()
        self.event_kwargs = {}

    async def send(self, data):
        self._dispatch('socket_raw_send', data)
        if self.cur_event is None:
            raise ValueError("Unhandled Websocket send event")
        await _dispatch_event(self.cur_event, *self.event_args, **self.event_kwargs)
        self.cur_event = None
        self.event_args = ()
        self.event_kwargs = {}

    async def change_presence(self, *, activity=None, status=None, afk=False, since=0.0):
        self.cur_event = "presence"
        self.event_args = (activity, status, afk, since)
        await super().change_presence(activity=activity, status=status, afk=afk, since=since)


class FakeState(state.ConnectionState):

    def __init__(self, client, http, user=None, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        super().__init__(dispatch=client.dispatch, chunker=client._chunker, handlers=None, syncer=None, http=http,
                         loop=loop)
        if user is None:
            user = discord.ClientUser(state=self, data=facts.make_user_dict("FakeApp", "0001", None))
        self.user = user
        self.shard_count = client.shard_count
        self._get_websocket = lambda x: client.ws


def get_state():
    if _cur_config is None:
        raise ValueError("Discord class factories not configured")
    return _cur_config.state


def set_callback(cb, event):
    _cur_config.callbacks[event] = cb


def get_callback(event):
    if _cur_config.callbacks.get(event) is None:
        raise ValueError(f"Callback for event {event} not set")
    return _cur_config.callbacks[event]


def remove_callback(event):
    return _cur_config.callbacks.pop(event, None)


async def _dispatch_event(event, *args, **kwargs):
    cb = _cur_config.callbacks.get(event)
    if cb is not None:
        try:
            await cb(*args, **kwargs)
        except Exception as e:
            log.error(f"Error in handler for event {event}: {e}")


def make_guild(name, members=None, channels=None, roles=None, owner=False, id_num=-1):
    if id_num == -1:
        id_num = facts.make_id()
    if roles is None:
        roles = [facts.make_role_dict("@everyone", id_num)]
    if channels is None:
        channels = []
    if members is None:
        members = []
    member_count = len(members) if len(members) != 0 else 1

    state = get_state()

    owner_id = state.user.id if owner else 0

    guild = discord.Guild(
        state=state,
        data=facts.make_guild_dict(name, owner_id, roles, id_num=id_num, member_count=member_count, members=members,
                                   channels=channels)
    )
    state._add_guild(guild)
    return guild


def make_role(name, guild, id_num=-1, colour=0, permissions=104324161, hoist=False, mentionable=False):
    role = discord.Role(
        state=get_state(),
        guild=guild,
        data=facts.make_role_dict(
            name, id_num=id_num, colour=colour, permissions=permissions, hoist=hoist, mentionable=mentionable
        )
    )
    guild._add_role(role)
    return role


def make_text_channel(name, guild, position=-1, id_num=-1):
    if position == -1:
        position = len(guild.channels) + 1
    channel = discord.TextChannel(
        state=get_state(),
        guild=guild,
        data=facts.make_text_channel_dict(name, id_num, position=position)
    )
    guild._add_channel(channel)
    return channel


def make_user(username, discrim, avatar=None, id_num=-1):
    if id_num == -1:
        id_num = facts.make_id()
    return discord.User(
        state=get_state(),
        data=facts.make_user_dict(username, discrim, avatar, id_num)
    )


def make_member(user, guild, nick=None, roles=None):
    if roles is None:
        roles = []
    roles = list(map(lambda x: x.id, roles))
    member = discord.Member(
        state=get_state(),
        guild=guild,
        data=facts.make_member_dict(user, roles, nick=nick)
    )
    guild._add_member(member)
    return member


def make_message(content, author, channel, id_num=-1):
    return discord.Message(
        state=get_state(),
        channel=channel,
        data=facts.make_message_dict(channel, author, id_num, content=content, guild_id=channel.guild.id)
    )


def make_attachment(filename, name=None, id_num=-1):
    if name is None:
        name = str(filename.name)
    if not filename.is_file():
        raise ValueError("Attachment must be a real file")
    size = filename.stat().st_size
    file_uri = filename.absolute().as_uri()
    return discord.Attachment(
        state=get_state(),
        data=facts.make_attachment_dict(name, size, file_uri, file_uri, id_num)
    )


def configure(client):
    global _cur_config

    if not isinstance(client, discord.Client):
        raise TypeError("Runner client must be an instance of discord.Client")

    loop = asyncio.get_event_loop()

    if client.http is not None:
        loop.create_task(client.http.close())

    http = FakeHttp(loop=loop)
    client.http = http

    ws = FakeWebSocket()
    client.ws = ws

    test_state = FakeState(client, http=http, loop=loop)
    http.state = test_state

    client._connection = test_state

    _cur_config = BackendConfig({}, test_state)


def main():
    print(facts.make_id())

    d_user = make_user("Test", "0001")
    d_guild = make_guild("Test_Guild")
    d_channel = make_text_channel("Channel 1", d_guild)
    d_member = make_member(d_user, d_guild)

    print(d_user, d_member, d_channel)


if __name__ == "__main__":
    main()
