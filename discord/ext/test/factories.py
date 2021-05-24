"""
    Module for (mostly) stateless creation/destructuring of discord.py objects. Primarily a utility
    for the rest of the library, which often needs to convert between objects and JSON at various stages.
"""

import typing
import datetime as dt
import discord
from . import _types

generated_ids: int = 0


def make_id() -> int:
    global generated_ids
    # timestamp
    discord_epoch = str(bin(int(dt.datetime.now().timestamp() * 1000) - 1420070400000))[2:]
    discord_epoch = "0" * (42 - len(discord_epoch)) + discord_epoch
    # internal worker id
    worker = "00001"
    # internal process id
    process = "00000"
    # determine how many ids have been generated so far
    generated = str(bin(generated_ids)[2:])
    generated_ids += 1
    generated = "0" * (12 - len(generated)) + generated
    # and now finally return the ID
    return int(discord_epoch + worker + process + generated, 2)


def _fill_optional(data: _types.JsonDict, obj: typing.Any, items: typing.Iterable[str]) -> None:
    if isinstance(obj, dict):
        for item in items:
            result = obj.pop(item, None)
            if result is None:
                continue
            data[item] = result
        if len(obj) > 0:
            print("Warning: Invalid attributes passed")
    else:
        for item in items:
            if hasattr(obj, item):
                data[item] = getattr(obj, item)


@typing.overload
def make_user_dict(
        username: str,
        discrim: typing.Union[str, int],
        avatar: typing.Optional[str],
        id_num: int = ...,
        flags: int = ...,
        *,
        bot: bool = ...,
        mfa_enabled: bool = ...,
        locale: str = ...,
        verified: bool = ...,
        email: str = ...,
        premium_type: int = ...,
) -> _types.JsonDict: ...


def make_user_dict(username: str, discrim: typing.Union[str, int], avatar: str, id_num: int = -1, flags: int = 0, **kwargs: typing.Any) -> _types.JsonDict:
    if isinstance(discrim, int):
        assert 0 < discrim < 10000
        discrim = f"{discrim:04}"
    elif isinstance(discrim, str):
        assert len(discrim) == 4 and discrim.isdigit() and 0 < int(discrim) < 10000
    if id_num < 0:
        id_num = make_id()
    out = {
        'id': id_num,
        'username': username,
        'discriminator': discrim,
        'avatar': avatar,
        'flags': flags
    }
    items = ("bot", "mfa_enabled", "locale", "verified", "email", "premium_type")
    _fill_optional(out, kwargs, items)
    return out


def dict_from_user(user: discord.User) -> _types.JsonDict:
    out = {
        'id': user.id,
        'username': user.name,
        'discriminator': user.discriminator,
        'avatar': user.avatar
    }
    items = ("bot", "mfa_enabled", "locale", "verified", "email", "premium_type")
    _fill_optional(out, user, items)
    return out


@typing.overload
def make_member_dict(
        guild: discord.Guild,
        user: discord.User,
        roles: typing.List[int],
        joined: int = ...,
        deaf: bool = ...,
        mute: bool = ...,
        voice: bool = ...,
        *,
        nick: str = ...,
) -> _types.JsonDict: ...


def make_member_dict(
        guild: discord.Guild,
        user: discord.User,
        roles: typing.List[int],
        joined: int = 0,
        deaf: bool = False,
        mute: bool = False,
        voice: bool = False,
        **kwargs: typing.Any,
) -> _types.JsonDict:
    out = {
        'guild_id': guild.id,
        'user': dict_from_user(user),
        'roles': roles,
        'joined_at': joined,
        'deaf': deaf,
        'mute': mute,
        'voice': voice,
    }
    items = ("nick",)
    _fill_optional(out, kwargs, items)
    return out


def dict_from_member(member: discord.Member) -> _types.JsonDict:
    voice_state = member.voice
    # discord code adds default role to every member later on in Member constructor
    roles_no_default = list(filter(lambda r: not r == member.guild.default_role, member.roles))
    out = {
        'guild_id': member.guild.id,
        'user': dict_from_user(member._user),
        'roles': list(map(lambda role: int(role.id), roles_no_default)),
        'joined_at': member.joined_at,
    }
    if voice_state is not None:
        out['deaf'] = voice_state.deaf
        out['mute'] = voice_state.mute
    items = ("nick",)
    _fill_optional(out, member, items)
    return out


# discord.py 1.7 bump requires the 'permissions_new', but if we keep 'permissions' then we seem to work on pre 1.7
def make_role_dict(
        name: str,
        id_num: int = -1,
        colour: int = 0,
        color: typing.Optional[int] = None,
        hoist: bool = False,
        position: int = -1,
        permissions: int = 104324161,
        managed: bool = False,
        mentionable: bool = False,
) -> _types.JsonDict:
    if id_num < 0:
        id_num = make_id()
    if color is not None:
        if colour != 0:
            raise ValueError("Both 'colour' and 'color' can be supplied at the same time")
        colour = color
    return {
        'id': id_num,
        'name': name,
        'color': colour,
        'hoist': hoist,
        'position': position,
        'permissions_new': permissions,
        'permissions': permissions,
        'managed': managed,
        'mentionable': mentionable
    }


# discord.py 1.7 bump requires the 'permissions_new', but if we keep 'permissions' then we seem to work on pre 1.7
def dict_from_role(role: discord.Role) -> _types.JsonDict:
    return {
        'id': role.id,
        'name': role.name,
        'color': role.colour.value,
        'hoist': role.hoist,
        'position': role.position,
        'permissions_new': role.permissions.value,
        'permissions': role.permissions.value,
        'managed': role.managed,
        'mentionable': role.mentionable
    }


@typing.overload
def make_channel_dict(
        ctype: int,
        id_num: int = ...,
        *,
        guild_id: int = ...,
        position: int = ...,
        permission_overwrites: _types.JsonDict = ...,
        name: str = ...,
        topic: typing.Optional[str] = ...,
        nsfw: bool = ...,
        last_message_id: typing.Optional[str] = ...,
        bitrate: int = ...,
        user_limit: int = ...,
        rate_limit_per_user: int = ...,
        recipients: typing.List[_types.JsonDict] = ...,
        icon: typing.Optional[str] = ...,
        owner_id: int = ...,
        application_id: int = ...,
        parent_id: typing.Optional[int] = ...,
        last_pin_timestamp: int = ...,
) -> _types.JsonDict: ...


def make_channel_dict(ctype: int, id_num: int = -1, **kwargs: typing.Any) -> _types.JsonDict:
    if id_num < 0:
        id_num = make_id()
    out = {
        'id': id_num,
        'type': ctype
    }
    items = ("guild_id", "position", "permission_overwrites", "name", "topic", "nsfw", "last_message_id", "bitrate",
             "user_limit", "rate_limit_per_user", "recipients", "icon", "owner_id", "application_id", "parent_id",
             "last_pin_timestamp")
    _fill_optional(out, kwargs, items)
    return out


@typing.overload
def make_text_channel_dict(
        name: str,
        id_num: int = ...,
        guild_id: int = ...,
        position: int = ...,
        permission_overwrites: _types.JsonDict = ...,
        topic: typing.Optional[str] = ...,
        nsfw: bool = ...,
        last_message_id: typing.Optional[int] = ...,
        rate_limit_per_user: int = ...,
        parent_id: typing.Optional[int] = ...,
        last_pin_timestamp: int = ...,
) -> _types.JsonDict: ...


def make_text_channel_dict(name: str, id_num: int = -1, **kwargs: typing.Any) -> _types.JsonDict:
    return make_channel_dict(discord.ChannelType.text.value, id_num, name=name, **kwargs)


def make_category_channel_dict(name: str, id_num: int = -1, **kwargs: typing.Any) -> _types.JsonDict:
    return make_channel_dict(discord.ChannelType.category.value, id_num, name=name, **kwargs)


def make_dm_channel_dict(user: discord.User, id_num: int = -1, **kwargs: typing.Any) -> _types.JsonDict:
    return make_channel_dict(discord.ChannelType.private, id_num, recipients=[dict_from_user(user)], **kwargs)


def dict_from_overwrite(target: typing.Union[discord.Member, discord.Role], overwrite: discord.PermissionOverwrite) -> _types.JsonDict:
    allow, deny = overwrite.pair()
    ovr = {
        'id': target.id,
        'allow': allow.value,
        'deny': deny.value,
        'allow_new': allow.value,
        'deny_new': deny.value
    }
    if isinstance(target, discord.Role):
        ovr['type'] = 'role'
    else:
        ovr['type'] = 'member'
    return ovr


# TODO: support all channel attributes
def dict_from_channel(channel: _types.AnyChannel) -> _types.JsonDict:
    if isinstance(channel, discord.TextChannel):
        return {
            'name': channel.name,
            'position': channel.position,
            'id': channel.id,
            'guild_id': channel.guild.id,
            'permission_overwrites': [dict_from_overwrite(k, v) for k, v in channel.overwrites.items()],
            'type': channel.type,
            'parent_id': channel.category_id
        }
    if isinstance(channel, discord.CategoryChannel):
        return {
            'name': channel.name,
            'position': channel.position,
            'id': channel.id,
            'guild_id': channel.guild.id,
            'permission_overwrites': [dict_from_overwrite(k, v) for k, v in channel.overwrites.items()],
            'type': channel.type
        }


@typing.overload
def make_message_dict(
        channel: _types.AnyChannel,
        author: discord.user.BaseUser,
        id_num: int = ...,
        content: str = ...,
        timestamp: int = ...,
        edited_timestamp: typing.Optional[int] = ...,
        tts: bool = ...,
        mention_everyone: bool = ...,
        mentions: typing.List[typing.Union[discord.User, discord.Member]] = ...,
        mention_roles: typing.List[int] = ...,
        mention_channels: typing.List[_types.AnyChannel] = ...,
        attachments: typing.List[discord.Attachment] = ...,
        embeds: typing.List[discord.Embed] = ...,
        pinned: bool = ...,
        type: int = ...,
        *,
        guild_id: int = ...,
        member: discord.Member = ...,
        reactions: typing.List[discord.Reaction] = ...,
        nonce: typing.Optional[int] = ...,
        webhook_id: int = ...,
        activity: discord.Activity = ...,
        application: _types.JsonDict = ...
) -> _types.JsonDict: ...


# TODO: Convert attachments, reactions, activity, and application to a dict.
def make_message_dict(
        channel: _types.AnyChannel,
        author: discord.user.BaseUser,
        id_num: int = -1,
        content: str = None,
        timestamp: int = None,
        edited_timestamp: typing.Optional[int] = None,
        tts: bool = False,
        mention_everyone: bool = False,
        mentions: typing.List[discord.User] = None,
        mention_roles: typing.List[int] = None,
        mention_channels: typing.List[_types.AnyChannel] = None,
        attachments: typing.List[discord.Attachment] = None,
        embeds: typing.List[discord.Embed] = None,
        pinned: bool = False,
        type: int = 0,
        **kwargs,
) -> _types.JsonDict:
    if mentions is None:
        mentions = []
    if mention_roles is None:
        mention_roles = []
    if mention_channels is None:
        mention_channels = []
    if attachments is None:
        attachments = []
    if embeds is None:
        embeds = []

    if not content:
        content = ""
    if id_num < 0:
        id_num = make_id()
    if isinstance(channel, discord.abc.GuildChannel):
        kwargs["guild_id"] = channel.guild.id
    if isinstance(author, discord.Member):
        author = author._user
        kwargs["member"] = dict_from_user(author)
    if timestamp is None:
        timestamp = discord.utils.snowflake_time(id_num)
    mentions = list(map(dict_from_user, mentions)) if mentions else []
    mention_channels = list(map(_mention_from_channel, mention_channels)) if mention_channels else []
    attachments = list(map(dict_from_attachment, attachments)) if attachments else []
    embeds = list(map(discord.Embed.to_dict, embeds)) if embeds else []

    out = {
        'id': id_num,
        'channel_id': channel.id,
        'author': dict_from_user(author),
        'content': content,
        'timestamp': timestamp,
        'edited_timestamp': edited_timestamp,
        'tts': tts,
        'mention_everyone': mention_everyone,
        'mentions': mentions,
        'mention_roles': mention_roles,
        'attachments': attachments,
        'embeds': embeds,
        'pinned': pinned,
        'type': type
    }
    items = ('guild_id', 'member', 'reactions', 'nonce', 'webhook_id', 'activity', 'application')
    _fill_optional(out, kwargs, items)
    return out


def _mention_from_channel(channel: _types.AnyChannel) -> _types.JsonDict:
    out = {
        "id": channel.id,
        "type": str(channel.type),
        "guild_id": None,
        "name": None
    }
    if hasattr(channel, "guild"):
        out["guild_id"] = channel.guild.id
    if hasattr(channel, "name"):
        out["name"] = channel.name

    return out


def _mention_from_role(role: discord.Role) -> int:
    return role.id


def dict_from_message(message: discord.Message) -> _types.JsonDict:
    out = {
        'id': message.id,
        'author': dict_from_user(message.author),
        'mentions': list(map(dict_from_user, message.mentions)),
        'mention_roles': list(map(_mention_from_role, message.role_mentions)),
        'mention_channels': list(map(_mention_from_channel, message.channel_mentions)),
        'edited_timestamp': message._edited_timestamp,
        'embeds': list(map(discord.Embed.to_dict, message.embeds)),
        'attachments': list(map(dict_from_attachment, message.attachments)),
    }

    items = ('content', 'pinned', 'application', 'activity',
             'mention_everyone', 'tts', 'type', 'nonce')
    _fill_optional(out, message, items)
    return out


def make_attachment_dict(
        filename: str,
        size: int,
        url: str,
        proxy_url: str,
        id_num: int = -1,
        height: typing.Optional[int] = None,
        width: typing.Optional[int] = None,
        content_type: typing.Optional[int] = None
) -> _types.JsonDict:
    if id_num < 0:
        id_num = make_id()
    return {
        'id': id_num,
        'filename': filename,
        'size': size,
        'url': url,
        'proxy_url': proxy_url,
        'height': height,
        'width': width,
        'content_type': content_type
    }


def dict_from_attachment(attachment: discord.Attachment) -> _types.JsonDict:
    return {
        'id': attachment.id,
        'filename': attachment.filename,
        'size': attachment.size,
        'url': attachment.url,
        'proxy_url': attachment.proxy_url,
        'height': attachment.height,
        'width': attachment.width,
    }


# TODO: dict_from_emoji and make_emoji_dict

def make_emoji_dict():
    pass


def dict_from_emoji(emoji):
    return {

    }


@typing.overload
def make_guild_dict(
        name: str,
        owner_id: int,
        roles: typing.List[_types.JsonDict],
        id_num: int = ...,
        emojis: typing.List[_types.JsonDict] = ...,
        icon: typing.Optional[str] = ...,
        splash: typing.Optional[str] = ...,
        region: str = ...,
        afk_channel_id: int = ...,
        afk_timeout: int = ...,
        verification_level: int = ...,
        default_message_notifications: int = ...,
        explicit_content_filter: int = ...,
        features: typing.List[str] = ...,
        mfa_level: int = ...,
        application_id: int = ...,
        system_channel_id: int = ...,
        *,
        owner: bool = ...,
        permissions: int = ...,
        embed_enabled: bool = ...,
        embed_channel_id: int = ...,
        widget_enabled: bool = ...,
        widget_channel_id: int = ...,
        joined_at: int = ...,
        large: bool = ...,
        unavailable: bool = ...,
        member_count: int = ...,
        voice_states: typing.List[discord.VoiceState] = ...,
        members: typing.List[discord.Member] = ...,
        channels: typing.List[discord.abc.GuildChannel] = ...,
        presences: typing.List[discord.Activity] = ...,
) -> _types.JsonDict: ...


def make_guild_dict(
        name: str,
        owner_id: int,
        roles: typing.List[_types.JsonDict],
        id_num: int = -1,
        emojis: typing.Optional[typing.List[_types.JsonDict]] = None,
        icon: typing.Optional[str] = None,
        splash: typing.Optional[str] = None,
        region: str = "en_north",
        afk_channel_id: typing.Optional[int] = None,
        afk_timeout: int = 600,
        verification_level: int = 0,
        default_message_notifications: int = 0,
        explicit_content_filter: int = 0,
        features: typing.Optional[typing.List[str]] = None,
        mfa_level: int = 0,
        application_id: typing.Optional[int] = None,
        system_channel_id: typing.Optional[int] = None,
        **kwargs: typing.Any,
) -> _types.JsonDict:
    if id_num < 0:
        id_num = make_id()
    if emojis is None:
        emojis = []
    if features is None:
        features = []
    out = {
        'id': id_num,
        'name': name,
        'icon': icon,
        'splash': splash,
        'owner_id': owner_id,
        'region': region,
        'afk_channel_id': afk_channel_id,
        'afk_timeout': afk_timeout,
        'verification_level': verification_level,
        'default_message_notifications': default_message_notifications,
        'explicit_content_filter': explicit_content_filter,
        'roles': roles,
        'emojis': emojis,
        'members': [],
        'features': features,
        'mfa_level': mfa_level,
        'application_id': application_id,
        'system_channel_id': system_channel_id,
    }
    items = ("owner", "permissions", "embed_enabled", "embed_channel_id", "widget_enabled", "widget_channel_id",
             "joined_at", "large", "unavailable", "member_count", "voice_states", "members", "channels", "presences")
    _fill_optional(out, kwargs, items)
    return out


def dict_from_guild(guild: discord.Guild) -> _types.JsonDict:
    return {
        'id': guild.id,
        'name': guild.name,
        'icon': guild.icon,
        'splash': guild.splash,
        'owner_id': guild.owner_id,
        'region': guild.region,
        'afk_channel_id': guild.afk_channel.id if guild.afk_channel else None,
        'afk_timeout': guild.afk_timeout,
        'verification_level': guild.verification_level,
        'default_message_notifications': guild.default_notifications.value,
        'explicit_content_filter': guild.explicit_content_filter,
        'roles': list(map(dict_from_role, guild.roles)),
        'emojis': list(map(dict_from_emoji, guild.emojis)),
        'features': guild.features,
        'mfa_level': guild.mfa_level,
        'application_id': None,
        'system_channel_id': guild.system_channel.id if guild.system_channel else None,
        'owner': guild.owner_id == guild.me.id
    }
