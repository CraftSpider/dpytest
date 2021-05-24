"""
    Module for 'server-side' state during testing. This module should contain
    methods for altering said server-side state, which then are responsible for triggering
    a ``parse_*`` call in the configured client state to inform the bot of the change.

    This setup matches discord's actual setup, where an HTTP call triggers a change on the server,
    which is then sent back to the bot as an event which is parsed and dispatched.
"""

import asyncio
import sys
import logging
import re
import typing
import discord
import discord.http as dhttp
import pathlib
import urllib.parse
import urllib.request

from . import factories as facts, state as dstate, callbacks, websocket, _types


class BackendState(typing.NamedTuple):
    """
        The dpytest backend, with all the state it needs to hold to be able to pretend to be
        discord. Generally only used internally, but exposed through :py:func:`get_state`
    """
    messages: typing.Dict[int, typing.List[_types.JsonDict]]
    state: dstate.FakeState


log = logging.getLogger("discord.ext.tests")
_cur_config: typing.Optional[BackendState] = None
_undefined = object()  # default value for when NoneType has special meaning


def _get_higher_locs(num: int) -> typing.Dict[str, typing.Any]:
    """
        Get the local variables from higher in the call-stack. Should only be used in FakeHttp for
        retrieving information not passed to it by its caller.

    :param num: How many calls up to retrieve from
    :return: The local variables of that call, as a dictionary
    """
    frame = sys._getframe(num + 1)
    locs = frame.f_locals
    del frame
    return locs


class FakeRequest(typing.NamedTuple):
    """
        A fake web response, for use with discord ``HTTPException``\ s
    """
    status: int
    reason: str


class FakeHttp(dhttp.HTTPClient):
    """
        A mock implementation of an ``HTTPClient``. Instead of actually sending requests to discord, it triggers
        a runner callback and calls the ``dpytest`` backend to update any necessary state and trigger any necessary
        fake messages to the client.
    """
    fileno: typing.ClassVar[int] = 0
    state: dstate.FakeState

    def __init__(self, loop: asyncio.AbstractEventLoop = None) -> None:
        if loop is None:
            loop = asyncio.get_event_loop()

        self.state = None

        super().__init__(connector=None, loop=loop)

    async def request(self, *args: typing.Any, **kwargs: typing.Any) -> typing.NoReturn:
        """
            Overloaded to raise a NotImplemented error informing the user that the requested operation
            isn't yet supported by ``dpytest``. To fix this, the method call that triggered this error should be
            overloaded below to instead trigger a callback and call the appropriate backend function.

        :param args: Arguments provided to the request
        :param kwargs: Keyword arguments provided to the request
        """
        route: discord.http.Route = args[0]
        raise NotImplementedError(
            f"Operation occured that isn't captured by the tests framework. This is dpytest's fault, please report"
            f"an issue on github. Debug Info: {route.method} {route.url} with {kwargs}"
        )

    async def create_channel(
            self,
            guild_id: int,
            channel_type: discord.ChannelType,
            *,
            reason: typing.Optional[str] = None,
            **options: typing.Any
    ) -> _types.JsonDict:
        locs = _get_higher_locs(1)
        guild = locs.get("self", None)
        name = locs.get("name", None)
        perms = options.get("permission_overwrites", None)
        parent_id = options.get("parent_id", None)

        if channel_type == discord.ChannelType.text.value:
            channel = make_text_channel(name, guild, permission_overwrites=perms, parent_id=parent_id)
        elif channel_type == discord.ChannelType.category.value:
            channel = make_category_channel(name, guild, permission_overwrites=perms)
        else:
            raise NotImplementedError(
                "Operation occurred that isn't captured by the tests framework. This is dpytest's fault, please report"
                "an issue on github. Debug Info: only TextChannels and CategoryChannels are currently supported."
            )
        return facts.dict_from_channel(channel)

    async def delete_channel(self, channel_id: int, *, reason: str = None) -> None:
        locs = _get_higher_locs(1)
        channel = locs.get("self", None)
        if channel.type.value == discord.ChannelType.text.value:
            delete_channel(channel)
        if channel.type.value == discord.ChannelType.category.value:
            for sub_channel in channel.text_channels:
                delete_channel(sub_channel)
            delete_channel(channel)

    async def get_channel(self, channel_id: int) -> _types.JsonDict:
        await callbacks.dispatch_event("get_channel", channel_id)

        find = None
        for guild in _cur_config.state.guilds:
            for channel in guild.channels:
                if channel.id == channel_id:
                    find = facts.dict_from_channel(channel)
        if find is None:
            raise discord.errors.NotFound(FakeRequest(404, "Not Found"), "Unknown Channel")
        return find

    async def start_private_message(self, user_id: int) -> _types.JsonDict:
        locs = _get_higher_locs(1)
        user = locs.get("self", None)

        await callbacks.dispatch_event("start_private_message", user)

        return facts.make_dm_channel_dict(user)

    async def send_message(
            self,
            channel_id: int,
            content: str,
            *,
            tts: bool = False,
            embed: typing.Optional[_types.JsonDict] = None,
            nonce: typing.Optional[int] = None,
            allowed_mentions: typing.Optional[_types.JsonDict] = None,
            message_reference: typing.Optional[_types.JsonDict] = None,
    ) -> _types.JsonDict:
        locs = _get_higher_locs(1)
        channel = locs.get("channel", None)

        embeds = []
        if embed:
            embeds = [discord.Embed.from_dict(embed)]
        user = self.state.user
        if hasattr(channel, "guild"):
            perm = channel.permissions_for(channel.guild.get_member(user.id))
        else:
            perm = channel.permissions_for(user)
        if not (perm.send_messages or perm.administrator):
            raise discord.errors.Forbidden(FakeRequest(403, "missing send_messages"), "send_messages")

        message = make_message(
            channel=channel, author=self.state.user, content=content, tts=tts, embeds=embeds, nonce=nonce
        )

        await callbacks.dispatch_event("send_message", message)

        return facts.dict_from_message(message)

    async def send_typing(self, channel_id: int) -> None:
        locs = _get_higher_locs(1)
        channel = locs.get("channel", None)

        await callbacks.dispatch_event("send_typing", channel)

    async def send_files(
            self,
            channel_id: int,
            *,
            files: typing.Iterable[discord.File],
            content: typing.Optional[str] = None,
            tts: bool = False,
            embed: typing.Optional[_types.JsonDict] = None,
            nonce: typing.Optional[int] = None,
            allowed_mentions: typing.Optional[_types.JsonDict] = None,
            message_reference: typing.Optional[_types.JsonDict] = None,
    ) -> _types.JsonDict:
        # allowed_mentions is being ignored.  It must be a keyword argument but I'm not yet certain what to use it for
        locs = _get_higher_locs(1)
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

        await callbacks.dispatch_event("send_message", message)

        return facts.dict_from_message(message)

    async def delete_message(self, channel_id: int, message_id: int, *, reason: typing.Optional[str] = None) -> None:
        locs = _get_higher_locs(1)
        message = locs.get("self", None)

        await callbacks.dispatch_event("delete_message", message.channel, message, reason=reason)

        delete_message(message)

    async def edit_message(self, channel_id: int, message_id: int, **fields: typing.Any) -> _types.JsonDict:
        locs = _get_higher_locs(1)
        message = locs.get("self", None)

        await callbacks.dispatch_event("edit_message", message.channel, message, fields)

        out = facts.dict_from_message(message)
        out.update(fields)
        return out

    async def add_reaction(self, channel_id: int, message_id: int, emoji: str) -> None:
        locs = _get_higher_locs(1)
        message = locs.get("self")
        # normally only the connected user can add a reaction, but for testing purposes we want to be able to force
        # the call from a specific user.
        user = locs.get("member", self.state.user)

        emoji = emoji  # TODO: Turn this back into class?

        await callbacks.dispatch_event("add_reaction", message, emoji)

        add_reaction(message, user, emoji)

    async def remove_reaction(self, channel_id: int, message_id: int, emoji: str, member_id: int) -> None:
        locs = _get_higher_locs(1)
        message = locs.get("self")
        member = locs.get("member")

        await callbacks.dispatch_event("remove_reaction", message, emoji, member)

        remove_reaction(message, member, emoji)

    async def remove_own_reaction(self, channel_id: int, message_id: int, emoji: str) -> None:
        locs = _get_higher_locs(1)
        message = locs.get("self")
        member = locs.get("member")

        await callbacks.dispatch_event("remove_own_reaction", message, emoji, member)

        remove_reaction(message, self.state.user, emoji)

    async def get_message(self, channel_id: int, message_id: int) -> _types.JsonDict:
        locs = _get_higher_locs(1)
        channel = locs.get("self")

        await callbacks.dispatch_event("get_message", channel, message_id)

        messages = _cur_config.messages[channel_id]
        find = next(filter(lambda m: m["id"] == message_id, messages), None)
        if find is None:
            raise discord.errors.NotFound(FakeRequest(404, "Not Found"), "Unknown Message")
        return find

    async def logs_from(
            self,
            channel_id: int,
            limit: int,
            before: typing.Optional[int] = None,
            after: typing.Optional[int] = None,
            around: typing.Optional[int] = None
    ) -> typing.List[_types.JsonDict]:
        locs = _get_higher_locs(1)
        his = locs.get("self", None)
        channel = his.channel

        await callbacks.dispatch_event("logs_from", channel, limit, before=None, after=None, around=None)

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

    async def kick(self, user_id: int, guild_id: int, reason: typing.Optional[str] = None) -> None:
        locs = _get_higher_locs(1)
        guild = locs.get("self", None)
        member = locs.get("user", None)

        await callbacks.dispatch_event("kick", guild, member, reason=reason)

        delete_member(member)

    async def ban(self, user_id: int, guild_id: int, delete_message_days: int = 1, reason: typing.Optional[str] = None) -> None:
        locs = _get_higher_locs(1)
        guild = locs.get("self", None)
        member = locs.get("user", None)

        await callbacks.dispatch_event("ban", guild, member, delete_message_days, reason=reason)

        delete_member(member)

    async def change_my_nickname(self, guild_id: int, nickname: str, *, reason: typing.Optional[str] = None) -> _types.JsonDict:
        locs = _get_higher_locs(1)
        me = locs.get("self", None)

        me.nick = nickname

        await callbacks.dispatch_event("change_nickname", nickname, me, reason=reason)

        return {"nick": nickname}

    async def edit_member(self, guild_id: int, user_id: int, *, reason: typing.Optional[str] = None, **fields: typing.Any) -> None:
        locs = _get_higher_locs(1)
        member = locs.get("self", None)

        await callbacks.dispatch_event("edit_member", fields, member, reason=reason)

    async def get_member(self, guild_id: int, member_id: int) -> _types.JsonDict:
        locs = _get_higher_locs(1)
        guild = locs.get("self", None)
        member = discord.utils.get(guild.members, id=member_id)

        return facts.dict_from_member(member)

    async def edit_role(self, guild_id: int, role_id: int, *, reason: typing.Optional[str] = None, **fields: typing.Any) -> _types.JsonDict:
        locs = _get_higher_locs(1)
        role = locs.get("self")
        guild = role.guild

        await callbacks.dispatch_event("edit_role", guild, role, fields, reason=reason)

        update_role(role, **fields)

        return facts.dict_from_role(role)

    async def delete_role(self, guild_id: int, role_id: int, *, reason: typing.Optional[str] = None) -> None:
        locs = _get_higher_locs(1)
        role = locs.get("self")
        guild = role.guild

        await callbacks.dispatch_event("delete_role", guild, role, reason=reason)

        delete_role(role)

    async def create_role(self, guild_id: int, *, reason: typing.Optional[str] = None, **fields: typing.Any) -> _types.JsonDict:
        locs = _get_higher_locs(1)
        guild = locs.get("self", None)

        data = facts.make_role_dict(**fields)
        # TODO: Replace with a backend make_role, to match other things
        role = discord.Role(state=get_state(), data=data, guild=guild)
        await callbacks.dispatch_event("create_role", guild, role, reason=reason)

        return facts.dict_from_role(role)

    async def move_role_position(self, guild_id: int, positions: typing.List[_types.JsonDict], *, reason: typing.Optional[str] = None) -> None:
        locs = _get_higher_locs(1)
        role = locs.get("self", None)
        guild = role.guild

        await callbacks.dispatch_event("move_role", guild, role, positions, reason=reason)

    async def add_role(self, guild_id: int, user_id: int, role_id: int, *, reason: typing.Optional[str] = None) -> None:
        locs = _get_higher_locs(1)
        member = locs.get("self", None)
        role = locs.get("role", None)

        await callbacks.dispatch_event("add_role", member, role, reason=reason)

    async def remove_role(self, guild_id: int, user_id: int, role_id: int, *, reason: typing.Optional[str] = None) -> None:
        locs = _get_higher_locs(1)
        member = locs.get("self", None)
        role = locs.get("role", None)

        await callbacks.dispatch_event("remove_role", member, role, reason=reason)

    async def application_info(self) -> _types.JsonDict:
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
        await callbacks.dispatch_event("app_info", appinfo)

        return data

    async def delete_channel_permissions(self, channel_id: int, target_id: int, *, reason: typing.Optional[str] = None) -> None:
        locs = _get_higher_locs(1)
        channel: discord.TextChannel = locs.get("self", None)
        target = locs.get("target", None)

        user = self.state.user
        perm: discord.Permissions = channel.permissions_for(channel.guild.get_member(user.id))
        if not (perm.administrator or perm.manage_permissions):
            raise discord.errors.Forbidden(FakeRequest(403, "missing manage_roles"), "manage_roles")

        update_text_channel(channel, target, None)

    async def edit_channel_permissions(
            self,
            channel_id: int,
            target_id: int,
            allow_value: int,
            deny_value: int,
            perm_type: str,
            *,
            reason: typing.Optional[str] = None
    ) -> None:
        locs = _get_higher_locs(1)
        channel: discord.TextChannel = locs.get("self", None)
        target = locs.get("target", None)

        user = self.state.user
        perm: discord.Permissions = channel.permissions_for(channel.guild.get_member(user.id))
        if not (perm.administrator or perm.manage_permissions):
            raise discord.errors.Forbidden(FakeRequest(403, "missing manage_roles"), "manage_roles")

        ovr = discord.PermissionOverwrite.from_pair(discord.Permissions(allow_value), discord.Permissions(deny_value))
        update_text_channel(channel, target, ovr)

    async def get_from_cdn(self, url: str) -> bytes:
        parsed_url = urllib.parse.urlparse(url)
        path = urllib.request.url2pathname(parsed_url.path)
        with open(path, 'rb') as fd:
            return fd.read()


def get_state() -> dstate.FakeState:
    """
        Get the current backend state, or raise an error if it hasn't been configured

    :return: Current backend state
    """
    if _cur_config is None:
        raise ValueError("Discord class factories not configured")
    return _cur_config.state


def make_guild(
        name: str,
        members: typing.List[discord.Member] = None,
        channels: typing.List[_types.AnyChannel] = None,
        roles: typing.List[discord.Role] = None,
        owner: bool = False,
        id_num: int = -1,
) -> discord.Guild:
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


def update_guild(guild: discord.Guild, roles: typing.List[discord.Role] = None) -> discord.Guild:
    data = facts.dict_from_guild(guild)

    if roles is not None:
        data["roles"] = list(map(facts.dict_from_role, roles))

    state = get_state()
    state.parse_guild_update(data)

    return guild


def make_role(
        name: str,
        guild: discord.Guild,
        id_num: int = -1,
        colour: int = 0,
        permissions: int = 104324161,
        hoist: bool = False,
        mentionable: bool = False,
) -> discord.Role:
    r_dict = facts.make_role_dict(
        name, id_num=id_num, colour=colour, permissions=permissions, hoist=hoist, mentionable=mentionable
    )
    # r_dict["position"] = max(map(lambda x: x.position, guild._roles.values())) + 1
    r_dict["position"] = 1

    data = {
        "guild_id": guild.id,
        "role": r_dict
    }

    state = get_state()
    state.parse_guild_role_create(data)

    return guild.get_role(r_dict["id"])


def update_role(
        role: discord.Role,
        colour: typing.Optional[int] = None,
        color: typing.Optional[int] = None,
        permissions: typing.Optional[int] = None,
        hoist: typing.Optional[bool] = None,
        mentionable: typing.Optional[bool] = None,
        name: typing.Optional[str] = None,
) -> discord.Role:
    data = {"guild_id": role.guild.id, "role": facts.dict_from_role(role)}
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
    if name is not None:
        data["role"]["name"] = name

    state = get_state()
    state.parse_guild_role_update(data)

    return role


def delete_role(role: discord.Role) -> None:
    state = get_state()
    state.parse_guild_role_delete({"guild_id": role.guild.id, "role_id": role.id})


def make_text_channel(
        name: str,
        guild: discord.Guild,
        position: int = -1,
        id_num: int = -1,
        permission_overwrites: typing.Optional[_types.JsonDict] = None,
        parent_id: typing.Optional[int] = None,
) -> discord.TextChannel:
    if position == -1:
        position = len(guild.channels) + 1

    c_dict = facts.make_text_channel_dict(name, id_num, position=position, guild_id=guild.id,
                                          permission_overwrites=permission_overwrites, parent_id=parent_id)

    state = get_state()
    state.parse_channel_create(c_dict)

    return guild.get_channel(c_dict["id"])


def make_category_channel(
        name: str,
        guild: discord.Guild,
        position: int = -1,
        id_num: int = -1,
        permission_overwrites: typing.Optional[_types.JsonDict] = None,
) -> discord.CategoryChannel:
    if position == -1:
        position = len(guild.categories) + 1
    c_dict = facts.make_category_channel_dict(name, id_num, position=position, guild_id=guild.id,
                                              permission_overwrites=permission_overwrites)
    state = get_state()
    state.parse_channel_create(c_dict)

    return guild.get_channel(c_dict["id"])


def delete_channel(channel: _types.AnyChannel) -> None:
    c_dict = facts.make_text_channel_dict(channel.name, id_num=channel.id, guild_id=channel.guild.id)

    state = get_state()
    state.parse_channel_delete(c_dict)


def update_text_channel(
        channel: discord.TextChannel,
        target: typing.Union[discord.User, discord.Role],
        override: typing.Optional[discord.PermissionOverwrite] = _undefined
) -> None:
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


def make_user(username: str, discrim: typing.Union[str, int], avatar: typing.Optional[str] = None, id_num: int = -1) -> discord.User:
    if id_num == -1:
        id_num = facts.make_id()

    data = facts.make_user_dict(username, discrim, avatar, id_num)

    state = get_state()
    user = state.store_user(data)

    return user


def make_member(user: typing.Union[discord.user.BaseUser, discord.abc.User], guild: discord.Guild, nick: typing.Optional[str] = None, roles: typing.Optional[typing.List[discord.Role]] = None) -> discord.Member:
    if roles is None:
        roles = []
    roles = list(map(lambda x: x.id, roles))

    data = facts.make_member_dict(guild, user, roles, nick=nick)

    state = get_state()
    state.parse_guild_member_add(data)

    return guild.get_member(user.id)


def update_member(member: discord.Member, nick: typing.Optional[str] = None, roles: typing.Optional[typing.List[discord.Role]] = None) -> discord.Member:
    data = facts.dict_from_member(member)
    if nick is not None:
        data["nick"] = nick
    if roles is not None:
        data["roles"] = list(map(lambda x: x.id, roles))

    state = get_state()
    state.parse_guild_member_update(data)

    return member


def delete_member(member: discord.Member) -> None:
    out = facts.dict_from_member(member)
    state = get_state()
    state.parse_guild_member_remove(out)


def make_message(
        content: str,
        author: typing.Union[discord.user.BaseUser, discord.abc.User],
        channel: _types.AnyChannel,
        tts: bool = False,
        embeds: typing.Optional[typing.List[discord.Embed]] = None,
        attachments: typing.Optional[typing.List[discord.Attachment]] = None,
        nonce: typing.Optional[int] = None,
        id_num: int = -1,
) -> discord.Message:
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


MEMBER_MENTION: typing.Pattern = re.compile(r"<@!?[0-9]{17,21}>", re.MULTILINE)
ROLE_MENTION: typing.Pattern = re.compile(r"<@&([0-9]{17,21})>", re.MULTILINE)
CHANNEL_MENTION: typing.Pattern = re.compile(r"<#[0-9]{17,21}>", re.MULTILINE)


def find_user_mentions(content: typing.Optional[str], guild: typing.Optional[discord.Guild]) -> typing.List[discord.Member]:
    if guild is None or content is None:
        return []  # TODO: Check for dm user mentions
    matches = re.findall(MEMBER_MENTION, content)
    return [discord.utils.get(guild.members, mention=match) for match in matches]  # noqa: E501


def find_role_mentions(content: typing.Optional[str], guild: typing.Optional[discord.Guild]) -> typing.List[int]:
    if guild is None or content is None:
        return []
    matches = re.findall(ROLE_MENTION, content)
    return matches


def find_channel_mentions(content: typing.Optional[str], guild: typing.Optional[discord.Guild]) -> typing.List[_types.AnyChannel]:
    if guild is None or content is None:
        return []
    matches = re.findall(CHANNEL_MENTION, content)
    return [discord.utils.get(guild.channels, mention=match) for match in matches]


def delete_message(message: discord.Message) -> None:
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


def make_attachment(filename: pathlib.Path, name: typing.Optional[str] = None, id_num: int = -1) -> discord.Attachment:
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


def add_reaction(message: discord.Message, user: typing.Union[discord.user.BaseUser, discord.abc.User], emoji: str) -> None:
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
    # when reactions are added by something other than the bot client, we want the user to end up in the payload.
    if isinstance(user, discord.Member):
        data["member"] = facts.dict_from_member(user)

    state = get_state()
    state.parse_message_reaction_add(data)

    messages = _cur_config.messages[message.channel.id]
    message_data = next(filter(lambda x: x["id"] == message.id, messages), None)
    if message_data is not None:
        if "reactions" not in message_data:
            message_data["reactions"] = []

        react: typing.Optional[_types.JsonDict] = None
        for react in message_data["reactions"]:
            if react["emoji"]["id"] == emoji["id"] and react["emoji"]["name"] == emoji["name"]:
                break

        if react is None:
            react = {"count": 0, "me": False, "emoji": emoji}
            message_data["reactions"].append(react)

        react["count"] += 1
        if user.id == state.user.id:
            react["me"] = True


def remove_reaction(message: discord.Message, user: discord.user.BaseUser, emoji: str) -> None:
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

        react: typing.Optional[_types.JsonDict] = None
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


@typing.overload
def configure(client: discord.Client) -> None: ...
@typing.overload
def configure(client: typing.Optional[discord.Client], *, use_dummy: bool = ...) -> None: ...


def configure(client: typing.Optional[discord.Client], *, use_dummy: bool = False) -> None:
    global _cur_config, _messages

    if client is None and use_dummy:
        log.info("None passed to backend configuration, dummy client will be used")
        client = discord.Client()

    if not isinstance(client, discord.Client):
        raise TypeError("Runner client must be an instance of discord.Client")

    loop = asyncio.get_event_loop()

    if client.http is not None:
        loop.create_task(client.http.close())

    http = FakeHttp(loop=loop)
    client.http = http

    ws = websocket.FakeWebSocket(None, loop=loop)
    client.ws = ws

    test_state = dstate.FakeState(client, http=http, loop=loop)
    http.state = test_state

    client._connection = test_state

    _cur_config = BackendState({}, test_state)


def main() -> None:
    print(facts.make_id())

    d_user = make_user("Test", "0001")
    d_guild = make_guild("Test_Guild")
    d_channel = make_text_channel("Channel 1", d_guild)
    d_member = make_member(d_user, d_guild)

    print(d_user, d_member, d_channel)


if __name__ == "__main__":
    main()
