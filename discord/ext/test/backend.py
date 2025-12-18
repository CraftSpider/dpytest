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
import datetime

import discord
import discord.http as dhttp
import pathlib
import urllib.parse
import urllib.request

from discord.types import member
from requests import Response
from typing import NamedTuple, Any, ClassVar, NoReturn, Literal, Pattern, overload, Sequence, Iterable

from . import factories as facts, state as dstate, callbacks, websocket, _types
from ._types import Undef, undefined
from discord.types.snowflake import Snowflake

from .callbacks import CallbackEvent


class BackendState(NamedTuple):
    """
        The dpytest backend, with all the state it needs to hold to be able to pretend to be
        discord. Generally only used internally, but exposed through :py:func:`get_state`
    """
    messages: dict[int, list[_types.message.Message]]
    state: dstate.FakeState


log = logging.getLogger("discord.ext.tests")
_cur_config: BackendState | None = None


def _get_higher_locs(num: int) -> dict[str, Any]:
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


class FakeRequest(Response):
    """
        A fake web response, for use with discord ``HTTPException``s
    """

    def __init__(self, status: int, reason: str):
        super().__init__()
        self.status = status
        self.status_code = status
        self.reason = reason


class FakeHttp(dhttp.HTTPClient):
    """
        A mock implementation of an ``HTTPClient``. Instead of actually sending requests to discord, it triggers
        a runner callback and calls the ``dpytest`` backend to update any necessary state and trigger any necessary
        fake messages to the client.
    """
    fileno: ClassVar[int] = 0
    state: dstate.FakeState

    def __init__(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        if loop is None:
            loop = asyncio.get_event_loop()

        self.state = None  # type: ignore[assignment]

        super().__init__(connector=None, loop=loop)

    async def request(
            self,
            route: discord.http.Route,
            *,
            files: Sequence[discord.File] | None = None,
            form: Iterable[dict[str, Any]] | None = None,
            **kwargs: Any,
    ) -> NoReturn:
        """
            Overloaded to raise a NotImplemented error informing the user that the requested operation
            isn't yet supported by ``dpytest``. To fix this, the method call that triggered this error should be
            overloaded below to instead trigger a callback and call the appropriate backend function.

        :param route: The route to request
        :param files: Sequence of files in the request
        :param form: Form input data
        :param kwargs: Any other request arguments
        """
        raise NotImplementedError(
            f"Operation occurred that isn't captured by the tests framework. This is dpytest's fault, please report"
            f"an issue on github. Debug Info: {route.method} {route.url} with {kwargs}"
        )

    async def create_channel(
            self,
            guild_id: Snowflake,
            channel_type: _types.channel.ChannelType,
            *,
            reason: str | None = None,
            **options: Any
    ) -> _types.channel.GuildChannel:
        locs = _get_higher_locs(1)
        guild = locs["self"]
        name = locs["name"]
        perms = options.get("permission_overwrites", None)
        parent_id = options.get("parent_id", None)

        channel: discord.abc.GuildChannel
        if channel_type == discord.ChannelType.text.value:
            channel = make_text_channel(name, guild, permission_overwrites=perms, parent_id=parent_id)
        elif channel_type == discord.ChannelType.category.value:
            channel = make_category_channel(name, guild, permission_overwrites=perms)
        elif channel_type == discord.ChannelType.voice.value:
            channel = make_voice_channel(name, guild, permission_overwrites=perms)

        else:
            raise NotImplementedError(
                "Operation occurred that isn't captured by the tests framework. This is dpytest's fault, please report"
                "an issue on github. Debug Info: only TextChannels and CategoryChannels are currently supported."
            )
        return facts.dict_from_object(channel)

    async def delete_channel(self, channel_id: Snowflake, *, reason: str | None = None) -> None:
        locs = _get_higher_locs(1)
        channel = locs["self"]
        if channel.type.value == discord.ChannelType.text.value:
            delete_channel(channel)
        if channel.type.value == discord.ChannelType.category.value:
            for sub_channel in channel.text_channels:
                delete_channel(sub_channel)
            delete_channel(channel)
        if channel.type.value == discord.ChannelType.voice.value:
            delete_channel(channel)

    async def get_channel(self, channel_id: Snowflake) -> _types.channel.Channel:
        await callbacks.dispatch_event(CallbackEvent.get_channel, channel_id)

        find = None
        for guild in get_state().guilds:
            for channel in guild.channels:
                if channel.id == channel_id:
                    find = facts.dict_from_object(channel)
        if find is None:
            raise discord.errors.NotFound(FakeRequest(404, "Not Found"), "Unknown Channel")
        return find

    async def start_private_message(self, user_id: Snowflake) -> _types.channel.DMChannel:
        locs = _get_higher_locs(1)
        user = locs["self"]

        await callbacks.dispatch_event(CallbackEvent.start_private_message, user)

        return facts.make_dm_channel_dict(user)

    async def send_message(
            self,
            channel_id: Snowflake,
            *,
            params: dhttp.MultipartParameters
    ) -> _types.message.Message:
        locs = _get_higher_locs(1)
        channel = locs["channel"]

        payload = params.payload

        embeds = []
        attachments = []
        content = ""
        tts = False
        nonce = None

        # EMBEDS
        if payload:
            content = payload.get("content") or ""
            tts = payload.get("tts") or False
            nonce = payload.get("nonce")
            if payload.get("embeds"):
                embeds = [discord.Embed.from_dict(e) for e in payload.get("embeds", [])]

        # ATTACHMENTS
        if params.files:
            paths = []
            for file in params.files:
                path = pathlib.Path(f"./dpytest_{FakeHttp.fileno}.dat")
                FakeHttp.fileno += 1
                if file.fp.seekable():
                    file.fp.seek(0)
                with open(path, "wb") as nfile:
                    nfile.write(file.fp.read())
                paths.append((path, file.filename))
            attachments = list(map(lambda x: make_attachment(*x), paths))

        user = self.state.user
        if channel.guild:
            perm = channel.permissions_for(channel.guild.get_member(user.id))
        else:
            perm = channel.permissions_for(user)
        if not (perm.send_messages or perm.administrator):
            raise discord.errors.Forbidden(FakeRequest(403, "missing send_messages"), "send_messages")

        message = make_message(channel=channel, author=self.state.user,
                               content=content,
                               tts=tts,
                               embeds=embeds,
                               attachments=attachments,
                               nonce=nonce
                               )
        await callbacks.dispatch_event(CallbackEvent.send_message, message)

        return facts.dict_from_object(message)

    async def send_typing(self, channel_id: Snowflake) -> None:
        locs = _get_higher_locs(1)
        channel = locs.get("channel", None)

        await callbacks.dispatch_event(CallbackEvent.send_typing, channel)

    async def delete_message(self, channel_id: Snowflake, message_id: Snowflake, *,
                             reason: str | None = None) -> None:
        locs = _get_higher_locs(1)
        message = locs["self"]

        await callbacks.dispatch_event(CallbackEvent.delete_message, message.channel, message, reason=reason)

        delete_message(message)

    async def edit_message(self, channel_id: Snowflake, message_id: Snowflake,
                           **fields: dhttp.MultipartParameters) -> _types.message.Message:  # noqa: E501
        locs = _get_higher_locs(1)
        message = locs["self"]

        await callbacks.dispatch_event(CallbackEvent.edit_message, message.channel, message, fields)

        return edit_message(message, **fields)

    async def add_reaction(self, channel_id: Snowflake, message_id: Snowflake,
                           emoji: str) -> None:
        locs = _get_higher_locs(1)
        message = locs["self"]
        # normally only the connected user can add a reaction, but for testing purposes we want to be able to force
        # the call from a specific user.
        user = locs.get("member", self.state.user)

        emoji = emoji  # TODO: Turn this back into class?

        await callbacks.dispatch_event(CallbackEvent.add_reaction, message, emoji)

        add_reaction(message, user, emoji)

    async def remove_reaction(self, channel_id: Snowflake, message_id: Snowflake,
                              emoji: str,
                              member_id: Snowflake) -> None:
        locs = _get_higher_locs(1)
        message = locs["self"]
        member = locs["member"]

        await callbacks.dispatch_event(CallbackEvent.remove_reaction, message, emoji, member)

        remove_reaction(message, member, emoji)

    async def remove_own_reaction(self, channel_id: Snowflake, message_id: Snowflake,
                                  emoji: str) -> None:
        locs = _get_higher_locs(1)
        message = locs["self"]
        member = locs["member"]

        await callbacks.dispatch_event(CallbackEvent.remove_own_reaction, message, emoji, member)

        remove_reaction(message, self.state.user, emoji)

    async def clear_reactions(self, channel_id: Snowflake, message_id: Snowflake) -> None:
        locs = _get_higher_locs(1)
        message = locs["self"]
        clear_reactions(message)

    async def get_message(self, channel_id: Snowflake,
                          message_id: Snowflake) -> _types.message.Message:
        locs = _get_higher_locs(1)
        channel = locs["self"]

        await callbacks.dispatch_event(CallbackEvent.get_message, channel, message_id)

        messages = get_config().messages[int(channel_id)]
        find = next(filter(lambda m: m["id"] == message_id, messages), None)
        if find is None:
            raise discord.errors.NotFound(FakeRequest(404, "Not Found"), "Unknown Message")
        return find

    async def logs_from(
            self,
            channel_id: Snowflake,
            limit: int,
            before: Snowflake | None = None,
            after: Snowflake | None = None,
            around: Snowflake | None = None
    ) -> list[_types.message.Message]:
        locs = _get_higher_locs(1)
        channel = locs["self"]

        await callbacks.dispatch_event(CallbackEvent.logs_from, channel, limit, before=None, after=None, around=None)

        messages = get_config().messages[int(channel_id)]
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

    async def kick(self, user_id: Snowflake, guild_id: Snowflake,
                   reason: str | None = None) -> None:
        locs = _get_higher_locs(1)
        guild = locs["self"]
        member = locs["user"]

        await callbacks.dispatch_event(CallbackEvent.kick, guild, member, reason=reason)

        delete_member(member)

    async def ban(self, user_id: Snowflake, guild_id: Snowflake,
                  delete_message_days: int = 1,
                  reason: str | None = None) -> None:
        locs = _get_higher_locs(1)
        guild = locs["self"]
        member = locs["user"]

        await callbacks.dispatch_event(CallbackEvent.ban, guild, member, delete_message_days, reason=reason)

        delete_member(member)

    async def unban(self, user_id: Snowflake, guild_id: Snowflake, *,
                    reason: str | None = None) -> None:
        locs = _get_higher_locs(1)
        guild = locs["self"]
        member = locs["user"]
        await callbacks.dispatch_event(CallbackEvent.unban, guild, member, reason=reason)

    async def change_my_nickname(self, guild_id: Snowflake, nickname: str, *,
                                 reason: str | None = None) -> _types.member.Nickname:
        locs = _get_higher_locs(1)
        me = locs["self"]

        me.nick = nickname

        await callbacks.dispatch_event(CallbackEvent.change_nickname, nickname, me, reason=reason)

        return {"nick": nickname}

    async def edit_member(self, guild_id: Snowflake, user_id: Snowflake, *,
                          reason: str | None = None,
                          **fields: Any) -> _types.member.MemberWithUser:
        locs = _get_higher_locs(1)
        member = locs["self"]

        await callbacks.dispatch_event(CallbackEvent.edit_member, fields, member, reason=reason)
        member = update_member(member, nick=fields.get('nick'), roles=fields.get('roles'))
        return facts.dict_from_object(member)

    async def get_members(
        self, guild_id: Snowflake, limit: int, after: Snowflake | None
    ) -> list[member.MemberWithUser]:
        locs = _get_higher_locs(1)
        guild = locs["self"]
        return list(map(facts.dict_from_object, guild.members))

    async def get_member(self, guild_id: Snowflake,
                         member_id: Snowflake) -> _types.member.MemberWithUser:
        locs = _get_higher_locs(1)
        guild = locs["self"]
        member = discord.utils.get(guild.members, id=member_id)

        return facts.dict_from_object(member)

    async def edit_role(self, guild_id: Snowflake, role_id: Snowflake, *,
                        reason: str | None = None,
                        **fields: Any) -> _types.role.Role:
        locs = _get_higher_locs(1)
        role = locs["self"]
        guild = role.guild

        await callbacks.dispatch_event(CallbackEvent.edit_role, guild, role, fields, reason=reason)

        update_role(role, **fields)
        return facts.dict_from_object(role)

    async def delete_role(self, guild_id: Snowflake, role_id: Snowflake, *,
                          reason: str | None = None) -> None:
        locs = _get_higher_locs(1)
        role = locs["self"]
        guild = role.guild

        await callbacks.dispatch_event(CallbackEvent.delete_role, guild, role, reason=reason)

        delete_role(role)

    async def create_role(self, guild_id: Snowflake, *, reason: str | None = None,
                          **fields: Any) -> _types.role.Role:
        locs = _get_higher_locs(1)
        guild = locs["self"]
        role = make_role(guild=guild, **fields)

        await callbacks.dispatch_event(CallbackEvent.create_role, guild, role, reason=reason)

        return facts.dict_from_object(role)

    async def move_role_position(self, guild_id: Snowflake,
                                 positions: list[_types.guild.RolePositionUpdate], *,
                                 reason: str | None = None) -> list[_types.role.Role]:
        locs = _get_higher_locs(1)
        role = locs["self"]
        guild = role.guild

        await callbacks.dispatch_event(CallbackEvent.move_role, guild, role, positions, reason=reason)

        for pair in positions:
            guild._roles[pair["id"]].position = pair["position"]
        return list(guild._roles.values())

    async def add_role(self, guild_id: Snowflake, user_id: Snowflake,
                       role_id: Snowflake, *, reason: str | None = None) -> None:
        locs = _get_higher_locs(1)
        member = locs["self"]
        role = locs["role"]

        await callbacks.dispatch_event(CallbackEvent.add_role, member, role, reason=reason)

        roles = [role] + [x for x in member.roles if x.id != member.guild.id]
        update_member(member, roles=roles)

    async def remove_role(self, guild_id: Snowflake, user_id: Snowflake,
                          role_id: Snowflake, *,
                          reason: str | None = None) -> None:
        locs = _get_higher_locs(1)
        member = locs["self"]
        role = locs["role"]

        await callbacks.dispatch_event(CallbackEvent.remove_role, member, role, reason=reason)

        roles = [x for x in member.roles if x != role and x.id != member.guild.id]
        update_member(member, roles=roles)

    async def application_info(self) -> _types.appinfo.AppInfo:
        # TODO: make these values configurable
        user = self.state.user
        data: _types.appinfo.AppInfo = {
            "id": user.id,
            "name": user.name,
            "icon": user.avatar.url if user.avatar else None,
            "description": "A test discord application",
            "rpc_origins": [],
            "bot_public": True,
            "bot_require_code_grant": False,
            "owner": facts.make_user_dict("TestOwner", "0001", ""),
            "summary": "",
            "verify_key": "",
            "flags": 0,
        }

        appinfo = discord.AppInfo(self.state, data)
        await callbacks.dispatch_event(CallbackEvent.app_info, appinfo)

        return data

    async def delete_channel_permissions(self, channel_id: Snowflake,
                                         target_id: Snowflake, *,
                                         reason: str | None = None) -> None:
        locs = _get_higher_locs(1)
        channel: discord.TextChannel = locs["self"]
        target = locs["target"]

        user = self.state.user
        member = channel.guild.get_member(user.id)
        if member is None:
            raise RuntimeError(f"Couldn't find user {user.id} in guild {channel.guild.id}")
        perm: discord.Permissions = channel.permissions_for(member)
        if not (perm.administrator or perm.manage_permissions):
            raise discord.errors.Forbidden(FakeRequest(403, "missing manage_roles"), "manage_roles")

        update_text_channel(channel, target, None)

    async def edit_channel_permissions(
            self,
            channel_id: Snowflake,
            target_id: Snowflake,
            allow_value: str,
            deny_value: str,
            perm_type: Literal[0, 1],
            *,
            reason: str | None = None
    ) -> None:
        locs = _get_higher_locs(1)
        channel: discord.TextChannel = locs["self"]
        target = locs["target"]

        user = self.state.user
        member = channel.guild.get_member(user.id)
        if member is None:
            raise RuntimeError(f"Couldn't find user {user.id} in guild {channel.guild.id}")
        perm: discord.Permissions = channel.permissions_for(member)
        if not (perm.administrator or perm.manage_permissions):
            raise discord.errors.Forbidden(FakeRequest(403, "missing manage_roles"), "manage_roles")

        ovr = discord.PermissionOverwrite.from_pair(discord.Permissions(int(allow_value)),
                                                    discord.Permissions(int(deny_value)))
        update_text_channel(channel, target, ovr)

    async def get_from_cdn(self, url: str) -> bytes:
        parsed_url = urllib.parse.urlparse(url)
        path = urllib.request.url2pathname(parsed_url.path)
        with open(path, 'rb') as fd:
            return fd.read()

    async def get_user(self, user_id: Snowflake) -> _types.user.User:
        # return self.request(Route('GET', '/users/{user_id}', user_id=user_id))
        locs = _get_higher_locs(1)
        client = locs["self"]
        guild = client.guilds[0]
        member = discord.utils.get(guild.members, id=user_id)
        return facts.dict_from_object(member._user)

    async def pin_message(self, channel_id: Snowflake, message_id: Snowflake,
                          reason: str | None = None) -> None:
        # return self.request(Route('PUT', '/channels/{channel_id}/pins/{message_id}',
        #                          channel_id=channel_id, message_id=message_id), reason=reason)
        pin_message(channel_id, message_id)

    async def unpin_message(self, channel_id: Snowflake, message_id: Snowflake,
                            reason: str | None = None) -> None:
        # return self.request(Route('DELETE', '/channels/{channel_id}/pins/{message_id}',
        #                          channel_id=channel_id, message_id=message_id), reason=reason)
        unpin_message(channel_id, message_id)

    async def get_guilds(self, limit: int, before: Snowflake | None = None,
                         after: Snowflake | None = None,
                         with_counts: bool = True) -> list[_types.guild.Guild]:
        # self.request(Route('GET', '/users/@me/guilds')
        await callbacks.dispatch_event(
            CallbackEvent.get_guilds,
            limit,
            before=before,
            after=after,
            with_counts=with_counts,
        )
        guilds = get_state().guilds  # List[]

        guilds_new = [facts.dict_from_object(guild) for guild in guilds]

        if not limit:
            limit = 100
        if after is not None:
            start = next(i for i, v in enumerate(guilds) if v.id == after)
            return guilds_new[start:start + limit]
        else:
            if before is None:
                start = int(len(guilds) / 2)
            else:
                start = next(i for i, v in enumerate(guilds) if v.id == before)
            return guilds_new[start - limit: start]

    async def get_guild(self, guild_id: Snowflake, *, with_counts: bool = True) -> _types.guild.Guild:
        # return self.request(Route('GET', '/guilds/{guild_id}', guild_id=guild_id))
        # TODO: Respect with_counts
        locs = _get_higher_locs(1)
        client: discord.Client = locs["self"]
        guild = discord.utils.get(client.guilds, id=guild_id)
        if guild is None:
            raise RuntimeError(f"Couldn't find guild with ID {guild_id} in test client")
        return facts.dict_from_object(guild)


def get_state() -> dstate.FakeState:
    """
        Get the current backend state, or raise an error if it hasn't been configured

    :return: Current backend state
    """
    if _cur_config is None:
        raise ValueError("Dpytest backend not configured")
    return _cur_config.state


def get_config() -> BackendState:
    if _cur_config is None:
        raise ValueError("Dpytest backend not configured")
    return _cur_config


def make_guild(
        name: str,
        members: list[discord.Member] | None = None,
        channels: list[_types.AnyChannel] | None = None,
        roles: list[_types.role.Role] | None = None,
        owner: bool = False,
        id_num: int = -1,
) -> discord.Guild:
    """
        Add a new guild to the backend, triggering any relevant callbacks on the configured client

    :param name: Name of the guild
    :param members: Existing members of the guild or None
    :param channels: Existing channels in the guild or None
    :param roles: Existing roles in the guild or None
    :param owner: Whether the configured client owns the guild, default is false
    :param id_num: ID of the guild, or nothing to auto-generate
    :return: Newly created guild
    """
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

    data: _types.gateway.Guild = facts.make_guild_dict(
        name, owner_id, roles, id_num=id_num, member_count=member_count, members=members, channels=channels
    )

    state.parse_guild_create(data)

    return state._get_guild(id_num)  # type: ignore[return-value]


def update_guild(guild: discord.Guild, roles: list[discord.Role] | None = None) -> discord.Guild:
    """
        Update an existing guild with new information, triggers a guild update but not any individual item
        create/edit calls

    :param guild: Guild to be updated
    :param roles: New role list for the guild
    :return: Updated guild object
    """
    data = facts.dict_from_object(guild)

    if roles is not None:
        data["roles"] = list(map(facts.dict_from_object, roles))

    state = get_state()
    state.parse_guild_update(data)

    return guild


def make_role(
        name: str,
        guild: discord.Guild,
        id_num: int = -1,
        colour: int = 0,
        color: int | None = None,
        colors: _types.role.RoleColours | None = None,
        permissions: int = 104324161,
        hoist: bool = False,
        mentionable: bool = False,
) -> discord.Role:
    """
        Add a new role to the backend, triggering any relevant callbacks on the configured client

    :param name: Name of the new role
    :param guild: Guild role is being added to
    :param id_num: ID of the new role, or nothing to auto-generate
    :param colour: Color of the new role
    :param color: Alias for above
    :param colors: Colors for multi-color roles
    :param permissions: Permissions for the new role
    :param hoist: Whether the new role is hoisted
    :param mentionable: Whether the new role is mentionable
    :return: Newly created role
    """
    r_dict = facts.make_role_dict(
        name, id_num=id_num, colour=colour, color=color, colors=colors, permissions=str(permissions), hoist=hoist,
        mentionable=mentionable
    )
    # r_dict["position"] = max(map(lambda x: x.position, guild._roles.values())) + 1
    r_dict["position"] = 1

    data: _types.gateway._GuildRoleEvent = {
        "guild_id": guild.id,
        "role": r_dict
    }

    state = get_state()
    state.parse_guild_role_create(data)

    return guild.get_role(int(r_dict["id"]))  # type: ignore[return-value]


def update_role(
        role: discord.Role,
        colour: int | None = None,
        color: int | None = None,
        colors: _types.role.RoleColours | None = None,
        permissions: int | None = None,
        hoist: bool | None = None,
        mentionable: bool | None = None,
        name: str | None = None,
) -> discord.Role:
    """
        Update an existing role with new data, triggering a role update event.
        Any value not passed/passed None will not update the existing value.

    :param role: Role to update
    :param colour: New color for the role
    :param color: Alias for above
    :param colors: Colors for multi-color roles
    :param permissions: New permissions
    :param hoist: New hoist value
    :param mentionable: New mention value
    :param name: New name for the role
    :return: Role that was updated
    """
    data: _types.gateway._GuildRoleEvent = {
        "guild_id": role.guild.id,
        "role": facts.dict_from_object(role),
    }
    if color is not None:
        colour = color
    if colour is not None:
        data["role"]["color"] = colour
    if colors is not None:
        data["role"]["colors"] = colors
    if permissions is not None:
        data["role"]["permissions"] = str(permissions)

    if hoist is not None:
        data["role"]["hoist"] = hoist
    if mentionable is not None:
        data["role"]["mentionable"] = mentionable
    if name is not None:
        data["role"]["name"] = name

    state = get_state()
    state.parse_guild_role_update(data)

    return role


def delete_role(role: discord.Role) -> None:
    """
        Remove a role from the backend, deleting it from the guild

    :param role: Role to delete
    """
    state = get_state()
    state.parse_guild_role_delete({"guild_id": role.guild.id, "role_id": role.id})


def make_text_channel(
        name: str,
        guild: discord.Guild,
        position: int = -1,
        id_num: int = -1,
        permission_overwrites: _types.channel.PermissionOverwrite | None = None,
        parent_id: int | None = None,
) -> discord.TextChannel:
    if position == -1:
        position = len(guild.channels) + 1

    c_dict = facts.make_text_channel_dict(name, id_num, position=position, guild_id=guild.id,
                                          permission_overwrites=permission_overwrites, parent_id=parent_id)

    state = get_state()
    state.parse_channel_create(c_dict)

    return guild.get_channel(int(c_dict["id"]))  # type: ignore[return-value]


def make_category_channel(
        name: str,
        guild: discord.Guild,
        position: int = -1,
        id_num: int = -1,
        permission_overwrites: _types.channel.PermissionOverwrite | None = None,
) -> discord.CategoryChannel:
    if position == -1:
        position = len(guild.categories) + 1
    c_dict = facts.make_category_channel_dict(name, id_num, position=position, guild_id=guild.id,
                                              permission_overwrites=permission_overwrites)
    state = get_state()
    state.parse_channel_create(c_dict)

    return guild.get_channel(int(c_dict["id"]))  # type: ignore[return-value]


def make_voice_channel(
        name: str,
        guild: discord.Guild,
        position: int = -1,
        id_num: int = -1,
        permission_overwrites: _types.channel.PermissionOverwrite | None = None,
        parent_id: int | None = None,
        bitrate: int = 192,
        user_limit: int = 0

) -> discord.VoiceChannel:
    if position == -1:
        position = len(guild.voice_channels) + 1
    c_dict = facts.make_voice_channel_dict(name, id_num, position=position, guild_id=guild.id,
                                           permission_overwrites=permission_overwrites, parent_id=parent_id,
                                           bitrate=bitrate, user_limit=user_limit)
    state = get_state()
    state.parse_channel_create(c_dict)

    return guild.get_channel(int(c_dict["id"]))  # type: ignore[return-value]


def delete_channel(channel: discord.abc.GuildChannel) -> None:
    c_dict = facts.make_text_channel_dict(channel.name, id_num=channel.id, guild_id=channel.guild.id)

    state = get_state()
    state.parse_channel_delete(c_dict)


def update_text_channel(
        channel: discord.TextChannel,
        target: discord.Member | discord.Role | discord.Object,
        override: discord.PermissionOverwrite | None | Undef = undefined
) -> None:
    c_dict = facts.dict_from_object(channel)
    if override is not undefined:
        ovr = c_dict.get("permission_overwrites", [])
        existing = [o for o in ovr if o.get("id") == target.id]
        if existing:
            ovr.remove(existing[0])
        if override:
            ovr = ovr + [facts.dict_from_object(override, target=target)]
        c_dict["permission_overwrites"] = ovr

    state = get_state()
    state.parse_channel_update(c_dict)


def make_user(username: str, discrim: str | int, avatar: str | None = None,
              id_num: int = -1) -> discord.User:
    if id_num == -1:
        id_num = facts.make_id()

    data = facts.make_user_dict(username, discrim, avatar, id_num)

    state = get_state()
    user = state.store_user(data)

    return user


def make_member(user: discord.user.BaseUser, guild: discord.Guild,
                nick: str | None = None,
                roles: list[discord.Role] | None = None) -> discord.Member:
    if roles is None:
        roles = []
    role_ids: list[Snowflake] = list(map(lambda x: x.id, roles))

    data: _types.gateway.GuildMemberAddEvent = {
        'guild_id': guild.id,
        **facts.make_member_dict(user, role_ids, nick=nick),
    }

    state = get_state()
    state.parse_guild_member_add(data)

    return guild.get_member(user.id)  # type: ignore[return-value]


def update_member(member: discord.Member, nick: str | None = None,
                  roles: list[discord.Role] | None = None) -> discord.Member:
    data = facts.dict_from_object(member)
    if nick is not None:
        data["nick"] = nick
    if roles is not None:
        data["roles"] = list(map(lambda x: x.id, roles))

    state = get_state()
    state.parse_guild_member_update(data)  # type: ignore[arg-type]

    return member


def delete_member(member: discord.Member) -> None:
    out = facts.dict_from_object(member)
    state = get_state()
    state.parse_guild_member_remove(out)  # type: ignore[arg-type]


def make_message(
        content: str,
        author: discord.user.BaseUser | discord.Member,
        channel: _types.AnyChannel,
        tts: bool = False,
        embeds: list[discord.Embed] | None = None,
        attachments: list[discord.Attachment] | None = None,
        nonce: int | None = None,
        id_num: int = -1,
) -> discord.Message:
    guild = channel.guild if hasattr(channel, "guild") else None
    guild_id = guild.id if guild else None

    mentions = find_member_mentions(content, guild)
    role_mentions = find_role_mentions(content, guild)
    channel_mentions = find_channel_mentions(content, guild)

    kwargs: dict[str, Any] = {}
    if nonce is not None:
        kwargs["nonce"] = nonce

    data = facts.make_message_dict(
        channel, author, id_num, content=content, mentions=mentions, tts=tts, embeds=embeds, attachments=attachments,
        mention_roles=role_mentions, mention_channels=channel_mentions, guild_id=guild_id, **kwargs
    )

    state = get_state()
    state.parse_message_create(data)

    messages = get_config().messages
    if channel.id not in messages:
        messages[channel.id] = []
    messages[channel.id].append(data)

    return state._get_message(int(data["id"]))  # type: ignore[return-value]


def edit_message(
        message: discord.Message, **fields: dhttp.MultipartParameters
) -> _types.message.Message:
    data = facts.dict_from_object(message)
    payload = fields["params"].payload
    # TODO : do something for files and stuff.
    # if params.files:
    #     return self.request(r, files=params.files, form=params.multipart)
    # else:
    #     return self.request(r, json=params.payload)
    data.update(payload)  # type: ignore[typeddict-item]

    config = get_config()
    i = 0
    while i < len(config.messages[message.channel.id]):
        if config.messages[message.channel.id][i].get("id") == data.get("id"):
            config.messages[message.channel.id][i] = data
        i += 1

    return data


MEMBER_MENTION: Pattern[str] = re.compile(r"<@!?([0-9]{17,21})>", re.MULTILINE)
ROLE_MENTION: Pattern[str] = re.compile(r"<@&([0-9]{17,21})>", re.MULTILINE)
CHANNEL_MENTION: Pattern[str] = re.compile(r"<#([0-9]{17,21})>", re.MULTILINE)


def find_member_mentions(content: str | None, guild: discord.Guild | None) -> list[discord.Member | discord.User]:
    if guild is None or content is None:
        return []  # TODO: Check for dm user mentions
    matches = re.findall(MEMBER_MENTION, content)
    return [discord.utils.get(guild.members, id=int(match)) for match in matches]  # type: ignore[misc]


def find_role_mentions(content: str | None, guild: discord.Guild | None) -> list[Snowflake]:
    if guild is None or content is None:
        return []
    matches = re.findall(ROLE_MENTION, content)
    return matches


def find_channel_mentions(content: str | None,
                          guild: discord.Guild | None
                          ) -> list[_types.AnyChannel]:
    if guild is None or content is None:
        return []
    matches = re.findall(CHANNEL_MENTION, content)
    return [discord.utils.get(guild.channels, id=int(match)) for match in matches]  # type: ignore[misc]


def delete_message(message: discord.Message) -> None:
    data: _types.gateway.MessageDeleteEvent = {
        "id": message.id,
        "channel_id": message.channel.id
    }
    if message.guild is not None:
        data["guild_id"] = message.guild.id

    state = get_state()
    state.parse_message_delete(data)

    messages = get_config().messages[message.channel.id]
    index = next(i for i, v in enumerate(messages) if v["id"] == message.id)
    del get_config().messages[message.channel.id][index]


def make_attachment(filename: pathlib.Path, name: str | None = None, id_num: int = -1) -> discord.Attachment:
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


def add_reaction(message: discord.Message, user: discord.user.BaseUser | discord.abc.User,
                 emoji: str) -> None:
    if ":" in emoji:
        temp = emoji.split(":")
        partial: _types.message.PartialEmoji = {
            "id": temp[0],
            "name": temp[1]
        }
    else:
        partial = {
            "id": None,
            "name": emoji
        }

    data: _types.gateway.MessageReactionAddEvent = {
        "message_id": message.id,
        "channel_id": message.channel.id,
        "user_id": user.id,
        "emoji": partial,
        "burst": False,
        "type": 0,
    }
    if message.guild:
        data["guild_id"] = message.guild.id
    # when reactions are added by something other than the bot client, we want the user to end up in the payload.
    if isinstance(user, discord.Member):
        data["member"] = facts.dict_from_object(user)

    state = get_state()
    state.parse_message_reaction_add(data)

    messages = get_config().messages[message.channel.id]
    message_data = next(filter(lambda x: x["id"] == message.id, messages), None)
    if message_data is not None:
        if "reactions" not in message_data:
            message_data["reactions"] = []

        react: _types.message.Reaction | None = None
        for react in message_data["reactions"]:
            if react["emoji"]["id"] == partial["id"] and react["emoji"]["name"] == partial["name"]:
                break

        if react is None:
            react = {
                "count": 0,
                "me": False,
                "emoji": partial,
                "me_burst": False,
                "count_details": {
                    "burst": 0,
                    "normal": 0,
                },
                "burst_colors": [],
            }
            message_data["reactions"].append(react)

        react["count"] += 1
        react["count_details"]["normal"] += 1
        if user.id == state.user.id:
            react["me"] = True


def remove_reaction(message: discord.Message, user: discord.utils.Snowflake, emoji: str) -> None:
    if ":" in emoji:
        temp = emoji.split(":")
        partial: _types.message.PartialEmoji = {
            "id": temp[0],
            "name": temp[1]
        }
    else:
        partial = {
            "id": None,
            "name": emoji
        }

    data: _types.gateway.MessageReactionRemoveEvent = {
        "message_id": message.id,
        "channel_id": message.channel.id,
        "user_id": user.id,
        "emoji": partial,
        "burst": False,
        "type": 0,
    }
    if message.guild:
        data["guild_id"] = message.guild.id

    state = get_state()
    state.parse_message_reaction_remove(data)

    messages = get_config().messages[message.channel.id]
    message_data = next(filter(lambda x: x["id"] == message.id, messages), None)
    if message_data is not None:
        if "reactions" not in message_data:
            message_data["reactions"] = []

        react: _types.message.Reaction | None = None
        for react in message_data["reactions"]:
            if react["emoji"]["id"] == partial["id"] and react["emoji"]["name"] == partial["name"]:
                break
        if react is None:
            return

        react["count"] -= 1
        react["count_details"]["normal"] -= 1
        if user.id == state.user.id:
            react["me"] = False

        if react["count"] == 0:
            message_data["reactions"].remove(react)


def clear_reactions(message: discord.Message) -> None:
    data: _types.gateway.MessageReactionRemoveAllEvent = {
        "message_id": message.id,
        "channel_id": message.channel.id
    }
    if message.guild:
        data["guild_id"] = message.guild.id

    state = get_state()
    state.parse_message_reaction_remove_all(data)

    messages = get_config().messages[message.channel.id]
    message_data = next(filter(lambda x: x["id"] == message.id, messages), None)
    if message_data is not None:
        message_data["reactions"] = []


def pin_message(channel_id: Snowflake, message_id: Snowflake) -> None:
    data: _types.gateway.ChannelPinsUpdateEvent = {
        "channel_id": channel_id,
        "last_pin_timestamp": datetime.datetime.now().isoformat(),
    }
    state = get_state()
    state.parse_channel_pins_update(data)


def unpin_message(channel_id: Snowflake, message_id: Snowflake) -> None:
    data: _types.gateway.ChannelPinsUpdateEvent = {
        "channel_id": channel_id,
        "last_pin_timestamp": None,
    }
    state = get_state()
    state.parse_channel_pins_update(data)


@overload
def configure(client: discord.Client) -> None: ...


@overload
def configure(client: discord.Client | None, *, use_dummy: bool = ...) -> None: ...


def configure(client: discord.Client | None, *, use_dummy: bool = False) -> None:
    """
        Configure the backend, optionally with the provided client

    :param client: Client to use, or None
    :param use_dummy: Whether to use a dummy if client param is None, or error
    """
    global _cur_config

    if client is None and use_dummy:
        log.info("None passed to backend configuration, dummy client will be used")
        client = discord.Client(intents=discord.Intents.all())

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
