"""
    Functions and classes for building various discord.py classes
"""

import asyncio
import sys
import logging
import re
import typing
import pathlib
import discord
import discord.state as dstate
import discord.http as dhttp
import discord.gateway as gate

from . import factories as facts


class BackendConfig(typing.NamedTuple):
    callbacks: typing.Dict[str, typing.Callable[[typing.Any], typing.Coroutine]]
    messages: typing.Dict[int, typing.List[typing.Dict[str, typing.Any]]]
    state: "FakeState"


log = logging.getLogger("discord.ext.tests")
_cur_config: typing.Optional[BackendConfig] = None
_undefined = object()  # default value for when NoneType has special meaning


class FakeRequest(typing.NamedTuple):
    status: int
    reason: str


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
        route: discord.http.Route = args[0]
        raise NotImplementedError(
            f"Operation occured that isn't captured by the tests framework. This is dpytest's fault, please report"
            f"an issue on github. Debug Info: {route.method} {route.url} with {kwargs}"
        )

    async def start_private_message(self, user_id):
        locs = self._get_higher_locs(1)
        user = locs.get("self", None)

        await _dispatch_event("start_private_message", user)

        return facts.make_dm_channel_dict(user)

    async def send_message(self, channel_id, content, *, tts=False, embed=None, nonce=None):
        locs = self._get_higher_locs(1)
        channel = locs.get("channel", None)

        embeds = []
        if embed:
            embeds = [discord.Embed.from_dict(embed)]
        user = self.state.user
        if hasattr(channel, "guild"):
            perm = channel.permissions_for(channel.guild.get_member(user.id))
        else:
            perm = channel.permissions_for(user)
        if not ((perm.send_messages and perm.read_messages) or perm.administrator):
            raise discord.errors.Forbidden(FakeRequest(403, "missing send_messages"), "send_messages")

        message = make_message(
            channel=channel, author=self.state.user, content=content, tts=tts, embeds=embeds, nonce=nonce
        )

        await _dispatch_event("send_message", message)

        return facts.dict_from_message(message)

    async def send_typing(self, channel_id):
        locs = self._get_higher_locs(1)
        channel = locs.get("channel", None)

        await _dispatch_event("send_typing", channel)

    async def send_files(self, channel_id, *, files, content=None, tts=False, embed=None, nonce=None):
        locs = self._get_higher_locs(1)
        channel = locs.get("channel", None)

        attachments = []
        for file in files:
            path = pathlib.Path(f"./dpytest_{self.fileno}.dat")
            self.fileno += 1
            if file.fp.seekable():
                file.fp.seek(0)
            with open(path, "wb") as nfile:
                nfile.write(file.fp.read())
            attachments.append((path, file.filename))
        attachments = list(map(lambda x: make_attachment(*x), attachments))

        embeds = []
        if embed:
            embeds = [discord.Embed.from_dict(embed)]

        message = make_message(
            channel=channel, author=self.state.user, attachments=attachments, content=content, tts=tts, embeds=embeds,
            nonce=nonce
        )

        await _dispatch_event("send_message", message)

        return facts.dict_from_message(message)

    async def delete_message(self, channel_id, message_id, *, reason=None):
        locs = self._get_higher_locs(1)
        message = locs.get("self", None)

        await _dispatch_event("delete_message", message.channel, message, reason=reason)

    async def edit_message(self, channel_id, message_id, **fields):
        locs = self._get_higher_locs(1)
        message = locs.get("self", None)

        await _dispatch_event("edit_message", message.channel, message, fields)

        out = facts.dict_from_message(message)
        out.update(fields)
        return out

    async def add_reaction(self, channel_id, message_id, emoji):
        locs = self._get_higher_locs(1)
        message = locs.get("self")
        emoji = emoji  # TODO: Turn this back into class?

        await _dispatch_event("add_reaction", message, emoji)

        add_reaction(message, self.state.user, emoji)

    async def remove_reaction(self, channel_id, message_id, emoji, member_id):
        locs = self._get_higher_locs(1)
        message = locs.get("self")
        member = locs.get("member")

        await _dispatch_event("remove_reaction", message, emoji, member)

        remove_reaction(message, member, emoji)

    async def remove_own_reaction(self, channel_id, message_id, emoji):
        locs = self._get_higher_locs(1)
        message = locs.get("self")
        member = locs.get("member")

        await _dispatch_event("remove_own_reaction", message, emoji, member)

        remove_reaction(message, self.state.user, emoji)

    async def get_message(self, channel_id, message_id):
        locs = self._get_higher_locs(1)
        channel = locs.get("self")

        await _dispatch_event("get_message", channel, message_id)

        messages = _cur_config.messages[channel_id]
        find = next(filter(lambda m: m["id"] == message_id, messages), None)
        if find is None:
            raise discord.errors.NotFound(FakeRequest(404, "Not Found"), "Unknown Message")
        return find

    async def logs_from(self, channel_id, limit, before=None, after=None, around=None):
        locs = self._get_higher_locs(1)
        his = locs.get("self", None)
        channel = his.channel

        await _dispatch_event("logs_from", channel, limit, before=None, after=None, around=None)

        messages = _cur_config.messages[channel_id]
        if after is not None:
            start = next(i for i, v in enumerate(messages) if v["id"] == after)
            return messages[start:start + limit]
        elif around is not None:
            start = next(i for i, v in enumerate(messages) if v["id"] == around)
            return messages[start - limit // 2:start + limit // 2]
        else:
            if before is None:
                start = len(messages)
            else:
                start = next(i for i, v in enumerate(messages) if v["id"] == before)
            return messages[start - limit:start]

    async def kick(self, user_id, guild_id, reason=None):
        locs = self._get_higher_locs(1)
        guild = locs.get("self", None)
        member = locs.get("user", None)

        await _dispatch_event("kick", guild, member, reason=reason)

    async def ban(self, user_id, guild_id, delete_message_days=1, reason=None):
        locs = self._get_higher_locs(1)
        guild = locs.get("self", None)
        member = locs.get("user", None)

        await _dispatch_event("ban", guild, member, delete_message_days, reason=reason)

    async def change_my_nickname(self, guild_id, nickname, *, reason=None):
        locs = self._get_higher_locs(1)
        me = locs.get("self", None)

        me.nick = nickname
        await _dispatch_event("change_nickname", nickname, me, reason=reason)

        return {"nick": nickname}

    async def edit_member(self, guild_id, user_id, *, reason=None, **fields):
        locs = self._get_higher_locs(1)
        member = locs.get("self", None)

        await _dispatch_event("edit_member", fields, member, reason=reason)

    async def edit_role(self, guild_id, role_id, *, reason=None, **fields):
        locs = self._get_higher_locs(1)
        role = locs.get("self")
        guild = role.guild

        await _dispatch_event("edit_role", guild, role, fields, reason=reason)

        return facts.dict_from_role(role)

    async def delete_role(self, guild_id, role_id, *, reason=None):
        locs = self._get_higher_locs(1)
        role = locs.get("self")
        guild = role.guild

        await _dispatch_event("delete_role", guild, role, reason=reason)

    async def create_role(self, guild_id, *, reason=None, **fields):
        locs = self._get_higher_locs(1)
        guild = locs.get("self", None)

        data = facts.make_role_dict(**fields)
        role = discord.Role(state=get_state(), data=data, guild=guild)
        await _dispatch_event("create_role", guild, role, reason=reason)

        return facts.dict_from_role(role)

    async def move_role_position(self, guild_id, positions, *, reason=None):
        locs = self._get_higher_locs(1)
        role = locs.get("self", None)
        guild = role.guild

        await _dispatch_event("move_role", guild, role, positions, reason=reason)

    async def add_role(self, guild_id, user_id, role_id, *, reason=None):
        locs = self._get_higher_locs(1)
        member = locs.get("self", None)
        role = locs.get("role", None)

        await _dispatch_event("add_role", member, role, reason=reason)

    async def remove_role(self, guild_id, user_id, role_id, *, reason=None):
        locs = self._get_higher_locs(1)
        member = locs.get("self", None)
        role = locs.get("role", None)

        await _dispatch_event("remove_role", member, role, reason=reason)

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
            "owner": facts.make_user_dict("TestOwner", "0001", None),
            "summary": None,
            "verify_key": None
        }

        appinfo = discord.AppInfo(self.state, data)
        await _dispatch_event("app_info", appinfo)

        return data

    async def delete_channel_permissions(self, channel_id, target_id, *, reason=None):
        locs = self._get_higher_locs(1)
        channel: discord.TextChannel = locs.get("self", None)
        target = locs.get("target", None)

        user = self.state.user
        perm: discord.Permissions = channel.permissions_for(channel.guild.get_member(user.id))
        if not (perm.administrator or perm.manage_permissions):
            raise discord.errors.Forbidden(FakeRequest(403, "missing manage_roles"), "manage_roles")

        update_text_channel(channel, target, None)

    async def edit_channel_permissions(self, channel_id, target_id, allow_value, deny_value, perm_type, *, reason=None):
        locs = self._get_higher_locs(1)
        channel: discord.TextChannel = locs.get("self", None)
        target = locs.get("target", None)

        user = self.state.user
        perm: discord.Permissions = channel.permissions_for(channel.guild.get_member(user.id))
        if not (perm.administrator or perm.manage_permissions):
            raise discord.errors.Forbidden(FakeRequest(403, "missing manage_roles"), "manage_roles")

        ovr = discord.PermissionOverwrite.from_pair(discord.Permissions(allow_value), discord.Permissions(deny_value))
        update_text_channel(channel, target, ovr)


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


class FakeState(dstate.ConnectionState):

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
        self._do_dispatch = True

        real_disp = self.dispatch

        def dispatch(*args, **kwargs):
            if not self._do_dispatch:
                return
            return real_disp(*args, **kwargs)

        self.dispatch = dispatch

    def stop_dispatch(self):
        self._do_dispatch = False

    def start_dispatch(self):
        self._do_dispatch = True


class FakeClient(discord.Client):
    pass


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
        roles = [facts.make_role_dict("@everyone", id_num, position=0)]
    if channels is None:
        channels = []
    if members is None:
        members = []
    member_count = len(members) if len(members) != 0 else 1

    state = get_state()

    owner_id = state.user.id if owner else 0

    data = facts.make_guild_dict(
        name, owner_id, roles, id_num=id_num, member_count=member_count, members=members, channels=channels
    )

    state.parse_guild_create(data)

    return state._get_guild(id_num)


def update_guild(guild, roles=None):
    data = facts.dict_from_guild(guild)

    if roles is not None:
        data["roles"] = list(map(facts.dict_from_role, roles))

    state = get_state()
    state.parse_guild_update(data)

    return guild


def make_role(name, guild, id_num=-1, colour=0, permissions=104324161, hoist=False, mentionable=False):
    r_dict = facts.make_role_dict(
        name, id_num=id_num, colour=colour, permissions=permissions, hoist=hoist, mentionable=mentionable
    )
    r_dict["position"] = max(map(lambda x: x.position, guild._roles.values())) + 1

    data = {
        "guild_id": guild.id,
        "role": r_dict
    }

    state = get_state()
    state.parse_guild_role_create(data)

    return guild.get_role(r_dict["id"])


def update_role(role, colour=None, color=None, permissions=None, hoist=None, mentionable=None):
    data = facts.dict_from_role(role)
    if color is not None:
        colour = color
    if colour is not None:
        data["color"] = colour
    if permissions is not None:
        data["permissions"] = permissions
    if hoist is not None:
        data["hoist"] = hoist
    if mentionable is not None:
        data["mentionable"] = mentionable

    state = get_state()
    state.parse_guild_role_update(data)

    return role


def delete_role(role):
    state = get_state()
    state.parse_guild_role_delete({"guild_id": role.guild.id, "role_id": role.id})


def make_text_channel(name, guild, position=-1, id_num=-1):
    if position == -1:
        position = len(guild.channels) + 1

    c_dict = facts.make_text_channel_dict(name, id_num, position=position, guild_id=guild.id)

    state = get_state()
    state.parse_channel_create(c_dict)

    return guild.get_channel(c_dict["id"])


def update_text_channel(channel, target, override=_undefined):
    c_dict = facts.dict_from_channel(channel)
    if override is not _undefined:
        ovr = c_dict.get("permission_overwrites", [])
        existing = [o for o in ovr if o.get("id") == target.id]
        if existing:
            ovr.remove(existing[0])
        if override:
            ovr = ovr + [facts.dict_from_overwrite(target, override)]
        c_dict["permission_overwrites"] = ovr

    state = get_state()
    state.parse_channel_update(c_dict)


def make_user(username, discrim, avatar=None, id_num=-1):
    if id_num == -1:
        id_num = facts.make_id()

    data = facts.make_user_dict(username, discrim, avatar, id_num)

    state = get_state()
    user = state.store_user(data)

    return user


def make_member(user, guild, nick=None, roles=None):
    if roles is None:
        roles = []
    roles = list(map(lambda x: x.id, roles))

    data = facts.make_member_dict(guild, user, roles, nick=nick)

    state = get_state()
    state.parse_guild_member_add(data)

    return guild.get_member(user.id)


def update_member(member, nick=None, roles=None):
    data = facts.dict_from_member(member)
    if nick is not None:
        data["nick"] = nick
    if roles is not None:
        data["roles"] = list(map(lambda x: x.id, roles))

    state = get_state()
    state.parse_guild_member_update(data)

    return member


def delete_member(member):
    out = facts.dict_from_member(member)
    state = get_state()
    state.parse_guild_member_remove(out)


def make_message(content, author, channel, tts=False, embeds=None, attachments=None, nonce=None, id_num=-1):
    guild = channel.guild if hasattr(channel, "guild") else None
    guild_id = guild.id if guild else None

    mentions = find_user_mentions(content, guild)
    role_mentions = find_role_mentions(content, guild)
    channel_mentions = find_channel_mentions(content, guild)

    kwargs = {}
    if nonce is not None:
        kwargs["nonce"] = nonce

    data = facts.make_message_dict(
        channel, author, id_num, content=content, mentions=mentions, tts=tts, embeds=embeds, attachments=attachments,
        mention_roles=role_mentions, mention_channels=channel_mentions, guild_id=guild_id, **kwargs
    )

    state = get_state()
    state.parse_message_create(data)

    if channel.id not in _cur_config.messages:
        _cur_config.messages[channel.id] = []
    _cur_config.messages[channel.id].append(data)

    return state._get_message(data["id"])


MEMBER_MENTION = re.compile(r"<@!?[0-9]{17,21}>", re.MULTILINE)
ROLE_MENTION = re.compile(r"<@&([0-9]{17,21})>", re.MULTILINE)
CHANNEL_MENTION = re.compile(r"<#[0-9]{17,21}>", re.MULTILINE)


def find_user_mentions(content, guild):
    if guild is None:
        return []  # TODO: Check for dm user mentions
    matches = re.findall(MEMBER_MENTION, content)
    return [discord.utils.get(guild.members, mention=match) for match in matches]  # noqa: E501


def find_role_mentions(content, guild):
    if guild is None:
        return []
    matches = re.findall(ROLE_MENTION, content)
    return matches


def find_channel_mentions(content, guild):
    if guild is None:
        return []
    matches = re.findall(CHANNEL_MENTION, content)
    return [discord.utils.get(guild.channels, mention=match) for match in matches]


def delete_message(message):
    data = {
        "id": message.id,
        "channel_id": message.channel.id
    }
    if message.guild is not None:
        data["guild_id"] = message.guild.id

    state = get_state()
    state.parse_message_delete(data)

    messages = _cur_config.messages[message.channel.id]
    index = next(i for i, v in enumerate(messages) if v["id"] == message.id)
    del _cur_config.messages[message.channel.id][index]


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


def add_reaction(message, user, emoji):
    if ":" in emoji:
        temp = emoji.split(":")
        emoji = {
            "id": temp[0],
            "name": temp[1]
        }
    else:
        emoji = {
            "id": None,
            "name": emoji
        }

    data = {
        "message_id": message.id,
        "channel_id": message.channel.id,
        "user_id": user.id,
        "emoji": emoji
    }
    if message.guild:
        data["guild_id"] = message.guild.id

    state = get_state()
    state.parse_message_reaction_add(data)

    messages = _cur_config.messages[message.channel.id]
    message_data = next(filter(lambda x: x["id"] == message.id, messages), None)
    if message_data is not None:
        if "reactions" not in message_data:
            message_data["reactions"] = []

        react = None
        for react in message_data["reactions"]:
            if react["emoji"]["id"] == emoji["id"] and react["emoji"]["name"] == emoji["name"]:
                break

        if react is None:
            react = {"count": 0, "me": False, "emoji": emoji}
            message_data["reactions"].append(react)

        react["count"] += 1
        if user.id == state.user.id:
            react["me"] = True


def remove_reaction(message, user, emoji):
    if ":" in emoji:
        temp = emoji.split(":")
        emoji = {
            "id": temp[0],
            "name": temp[1]
        }
    else:
        emoji = {
            "id": None,
            "name": emoji
        }

    data = {
        "message_id": message.id,
        "channel_id": message.channel.id,
        "user_id": user.id,
        "emoji": emoji
    }
    if message.guild:
        data["guild_id"] = message.guild.id

    state = get_state()
    state.parse_message_reaction_remove(data)

    messages = _cur_config.messages[message.channel.id]
    message_data = next(filter(lambda x: x["id"] == message.id, messages), None)
    if message_data is not None:
        if "reactions" not in message_data:
            message_data["reactions"] = []

        react = None
        for react in message_data["reactions"]:
            if react["emoji"]["id"] == emoji["id"] and react["emoji"]["name"] == emoji["name"]:
                break
        if react is None:
            return

        react["count"] -= 1
        if user.id == state.user.id:
            react["me"] = False

        if react["count"] == 0:
            message_data["reactions"].remove(react)


def configure(client, *, use_dummy=False):
    global _cur_config, _messages

    if client is None and use_dummy:
        log.info("None passed to backend configuration, dummy client will be used")
        client = FakeClient()

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

    _cur_config = BackendConfig({}, {}, test_state)


def main():
    print(facts.make_id())

    d_user = make_user("Test", "0001")
    d_guild = make_guild("Test_Guild")
    d_channel = make_text_channel("Channel 1", d_guild)
    d_member = make_member(d_user, d_guild)

    print(d_user, d_member, d_channel)


if __name__ == "__main__":
    main()
