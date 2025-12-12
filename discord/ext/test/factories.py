"""
    Module for (mostly) stateless creation/destructuring of discord.py objects. Primarily a utility
    for the rest of the library, which often needs to convert between objects and JSON at various stages.
"""
import functools
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


@typing.overload
def _fill_optional(
        data: _types.user.User,
        obj: discord.User | dict[str, typing.Any],
        items: typing.Iterable[str]
) -> None: ...


@typing.overload
def _fill_optional(
        data: _types.user.User,
        obj: discord.ClientUser | dict[str, typing.Any],
        items: typing.Iterable[str]
) -> None: ...


@typing.overload
def _fill_optional(
        data: _types.guild.Member,
        obj: discord.Member | dict[str, typing.Any],
        items: typing.Iterable[str]
) -> None: ...


@typing.overload
def _fill_optional(
        data: _types.guild.Guild,
        obj: discord.Guild | dict[str, typing.Any],
        items: typing.Iterable[str]
) -> None: ...


@typing.overload
def _fill_optional(
        data: _types.channel.PartialChannel,
        obj: _types.AnyChannel | dict[str, typing.Any],
        items: typing.Iterable[str]
) -> None: ...


@typing.overload
def _fill_optional(
        data: _types.message.Message,
        obj: discord.Message | dict[str, typing.Any],
        items: typing.Iterable[str]
) -> None: ...


@typing.overload
def _fill_optional(
        data: _types.emoji.Emoji,
        obj: discord.Emoji | dict[str, typing.Any],
        items: typing.Iterable[str]
) -> None: ...


@typing.overload
def _fill_optional(
        data: _types.sticker.GuildSticker,
        obj: discord.GuildSticker | dict[str, typing.Any],
        items: typing.Iterable[str]
) -> None: ...


def _fill_optional(data: dict[str, typing.Any], obj: typing.Any, items: typing.Iterable[str]) -> None:
    if isinstance(obj, dict):
        obj: dict[str, typing.Any]
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


def make_user_dict(username: str, discrim: str | int, avatar: str, id_num: int = -1, flags: int = 0,
                   **kwargs: typing.Any) -> _types.user.User:
    if isinstance(discrim, int):
        assert 0 < discrim < 10000
        discrim = f"{discrim:04}"
    elif isinstance(discrim, str):
        assert len(discrim) == 4 and discrim.isdigit() and 0 < int(discrim) < 10000
    if id_num < 0:
        id_num = make_id()
    out: _types.user.User = {
        'id': id_num,
        'global_name': None,
        'username': username,
        'discriminator': discrim,
        'avatar': avatar,
        'flags': flags,
    }
    items: typing.Final = ("bot", "mfa_enabled", "locale", "verified", "email", "premium_type")
    _fill_optional(out, kwargs, items)
    return out


def make_member_dict(
        guild: discord.Guild,
        user: discord.User,
        roles: list[int],
        joined: str | None = None,
        deaf: bool = False,
        mute: bool = False,
        flags: int = 0,
        **kwargs: typing.Any,
) -> _types.guild.Member:
    out: _types.guild.Member = {
        'guild_id': guild.id,
        'user': dict_from_object(user),
        'roles': roles,
        'joined_at': joined,
        'deaf': deaf,
        'mute': mute,
        'flags': flags,
    }
    items = ("nick",)
    _fill_optional(out, kwargs, items)
    return out


def user_with_member(user: discord.User | discord.Member) -> _types.member.UserWithMember:
    if isinstance(user, discord.Member):
        member = dict_from_object(user)
        user = user._user
    else:
        member = None
    out = dict_from_object(user)
    if member:
        out['member'] = member
    return out


@typing.overload
def dict_from_object(obj: discord.User) -> _types.user.User: ...


@typing.overload
def dict_from_object(obj: discord.Member) -> _types.member.MemberWithUser: ...


@typing.overload
def dict_from_object(obj: discord.Role) -> _types.role.Role: ...


@typing.overload
def dict_from_object(obj: discord.TextChannel) -> _types.channel.TextChannel: ...


@typing.overload
def dict_from_object(obj: discord.DMChannel) -> _types.channel.DMChannel: ...


@typing.overload
def dict_from_object(obj: discord.CategoryChannel) -> _types.channel.CategoryChannel: ...


@typing.overload
def dict_from_object(obj: discord.VoiceChannel) -> _types.channel.VoiceChannel: ...


@typing.overload
def dict_from_object(obj: discord.Message) -> _types.message.Message: ...


@typing.overload
def dict_from_object(obj: discord.Attachment) -> _types.message.Attachment: ...


@typing.overload
def dict_from_object(obj: discord.Emoji) -> _types.emoji.Emoji: ...


@typing.overload
def dict_from_object(obj: discord.Sticker) -> _types.sticker.Sticker: ...


@typing.overload
def dict_from_object(obj: discord.StageInstance) -> _types.channel.StageInstance: ...


@typing.overload
def dict_from_object(obj: discord.ScheduledEvent) -> _types.guild.GuildScheduledEvent: ...


@typing.overload
def dict_from_object(obj: discord.Guild) -> _types.guild.Guild: ...


@functools.singledispatch
def dict_from_object(obj: typing.Any) -> typing.Never:
    raise TypeError(f"Unrecognized discord model type {type(obj)}")


@dict_from_object.register(discord.ClientUser)
def _from_client_user(user: discord.ClientUser) -> _types.user.User:
    out: _types.user.User = {
        'id': user.id,
        'global_name': user.global_name,
        'username': user.name,
        'discriminator': user.discriminator,
        'avatar': user.avatar.url if user.avatar else None,
    }
    items = ("bot", "mfa_enabled", "locale", "verified", "email", "premium_type")
    _fill_optional(out, user, items)
    return out


@dict_from_object.register(discord.User)
def _from_user(user: discord.User) -> _types.user.User:
    out: _types.user.User = {
        'id': user.id,
        'global_name': user.global_name,
        'username': user.name,
        'discriminator': user.discriminator,
        'avatar': user.avatar.url if user.avatar else None,
    }
    items = ("bot", "mfa_enabled", "locale", "verified", "email", "premium_type")
    _fill_optional(out, user, items)
    return out


@dict_from_object.register(discord.Member)
def _from_member(member: discord.Member) -> _types.member.MemberWithUser:
    # discord code adds default role to every member later on in Member constructor
    roles_no_default = list(filter(lambda r: not r == member.guild.default_role, member.roles))
    out: _types.guild.Member = {
        'guild_id': member.guild.id,
        'user': dict_from_object(member._user),
        'roles': list(map(lambda role: int(role.id), roles_no_default)),
        'joined_at': str(int(member.joined_at.timestamp())) if member.joined_at else None,
        'flags': member.flags.value,
        'deaf': member.voice.deaf if member.voice else False,
        'mute': member.voice.mute if member.voice else False,
    }
    items = ("nick",)
    _fill_optional(out, member, items)
    return out


@dict_from_object.register(discord.Role)
def _from_role(role: discord.Role) -> _types.role.Role:
    return {
        'id': role.id,
        'name': role.name,
        'color': role.colour.value,
        'colors': {
            'primary_color': role.colour.value,
            'secondary_color': role.secondary_color.value if role.secondary_color else None,
            'tertiary_color': role.tertiary_color.value if role.tertiary_color else None,
        },
        'hoist': role.hoist,
        'position': role.position,
        'permissions': str(role.permissions.value),
        'managed': role.managed,
        'mentionable': role.mentionable,
        'flags': role.flags.value,
    }


# TODO: support all channel attributes
@dict_from_object.register(discord.TextChannel)
def _from_text_channel(channel: discord.TextChannel) -> _types.channel.TextChannel:
    return {
        'name': channel.name,
        'position': channel.position,
        'id': channel.id,
        'guild_id': channel.guild.id,
        'permission_overwrites': [dict_from_overwrite(k, v) for k, v in channel.overwrites.items()],
        'type': channel.type,
        'parent_id': channel.category_id,
        'nsfw': channel.nsfw,
    }


@dict_from_object.register(discord.DMChannel)
def _from_dm_channel(channel: discord.DMChannel) -> _types.channel.DMChannel:
    pass


@dict_from_object.register(discord.CategoryChannel)
def _from_category_channel(channel: discord.CategoryChannel) -> _types.channel.CategoryChannel:
    return {
        'name': channel.name,
        'position': channel.position,
        'id': channel.id,
        'guild_id': channel.guild.id,
        'permission_overwrites': [dict_from_overwrite(k, v) for k, v in channel.overwrites.items()],
        'type': channel.type,
        'nsfw': channel.nsfw,
        'parent_id': channel.category_id,
    }


@dict_from_object.register(discord.VoiceChannel)
def _from_voice_channel(channel: discord.VoiceChannel) -> _types.channel.VoiceChannel:
    return {
        'name': channel.name,
        'position': channel.position,
        'id': channel.id,
        'guild_id': channel.guild.id,
        'permission_overwrites': [dict_from_overwrite(k, v) for k, v in channel.overwrites.items()],
        'type': channel.type,
        'nsfw': channel.nsfw,
        'parent_id': channel.category_id,
        'bitrate': channel.bitrate,
        'user_limit': channel.user_limit,
    }


@dict_from_object.register(discord.Message)
def _from_message(message: discord.Message) -> _types.message.Message:
    if isinstance(message.author, discord.Member):
        member = dict_from_object(message.author)
        user = message.author._user
    else:
        member = None
        user = message.author
    out: _types.message.Message = {
        'id': message.id,
        'author': dict_from_object(user),
        'mentions': list(map(user_with_member, message.mentions)),
        'mention_roles': list(map(_mention_from_role, message.role_mentions)),
        'mention_channels': list(map(_mention_from_channel, message.channel_mentions)),
        'edited_timestamp': str(int(message.edited_at.timestamp())) if message.edited_at else None,
        'embeds': list(map(discord.Embed.to_dict, message.embeds)),
        'attachments': list(map(dict_from_object, message.attachments)),
        'channel_id': message.channel.id,
        'content': message.content,
        'timestamp': str(int(message.created_at.timestamp())),
        'tts': message.tts,
        'mention_everyone': message.mention_everyone,
        'pinned': message.pinned,
        'type': message.type.value,
    }
    if member:
        out['member'] = member

    items = ('content', 'pinned', 'activity',
             'mention_everyone', 'tts', 'type', 'nonce')
    _fill_optional(out, message, items)
    return out


@dict_from_object.register(discord.Attachment)
def _from_attachment(attachment: discord.Attachment) -> _types.message.Attachment:
    return {
        'id': attachment.id,
        'filename': attachment.filename,
        'size': attachment.size,
        'url': attachment.url,
        'proxy_url': attachment.proxy_url,
        'height': attachment.height,
        'width': attachment.width,
        'content_type': attachment.content_type,
    }


@dict_from_object.register(discord.Emoji)
def _from_emoji(emoji: discord.Emoji) -> _types.emoji.Emoji:
    out: _types.emoji.Emoji = {
        'id': emoji.id,
        'name': emoji.name,
    }
    items = ("roles", "user", "require_colons", "managed", "animated", "available")
    _fill_optional(out, emoji, items)
    return out


@dict_from_object.register(discord.Sticker)
def _from_sticker(sticker: discord.Sticker) -> _types.sticker.Sticker:
    if isinstance(sticker, discord.StandardSticker):
        out: _types.sticker.StandardSticker = {
            'id': sticker.id,
            'name': sticker.name,
            'description': sticker.description,
            'tags': ",".join(sticker.tags),
            'format_type': sticker.format.value,
            'type': 1,
            'sort_value': sticker.sort_value,
            'pack_id': sticker.pack_id,
        }
    elif isinstance(sticker, discord.GuildSticker):
        out: _types.sticker.GuildSticker = {
            'id': sticker.id,
            'name': sticker.name,
            'description': sticker.description,
            'tags': sticker.tags,
            'format_type': sticker.format.value,
            'type': 2,
            'available': sticker.available,
            'guild_id': sticker.guild_id,
        }
        items = ("user",)
        _fill_optional(out, sticker, items)
    else:
        raise TypeError(f"Invalid type for sticker {type(sticker)}")
    return out


@dict_from_object.register(discord.StageInstance)
def _from_stage_instance(stage_instance: discord.StageInstance) -> _types.channel.StageInstance:
    return {
        'id': stage_instance.id,
        'guild_id': stage_instance.guild.id,
        'channel_id': stage_instance.channel_id,
        'topic': stage_instance.topic,
        'privacy_level': stage_instance.privacy_level.value,
        'discoverable_disabled': stage_instance.discoverable_disabled,
        'guild_scheduled_event_id': stage_instance.scheduled_event_id,
    }


@dict_from_object.register(discord.ScheduledEvent)
def _from_scheduled_event(event: discord.ScheduledEvent) -> _types.guild.GuildScheduledEvent:
    if event.entity_type == discord.EntityType.stage_instance:
        out: _types.scheduled_event.StageInstanceScheduledEvent = {
            'id': event.id,
            'guild_id': event.guild_id,
            'entity_id': event.entity_id,
            'name': event.name,
            'scheduled_start_time': str(int(event.start_time.timestamp())),
            'privacy_level': event.privacy_level.value,
            'status': event.status.value,
            'entity_type': 1,
            'channel_id': event.channel_id or 0,
            'entity_metadata': None,
        }
        if event.end_time:
            out["scheduled_end_time"] = str(int(event.end_time.timestamp()))
    elif event.entity_type == discord.EntityType.voice:
        out: _types.scheduled_event.VoiceScheduledEvent = {
            'id': event.id,
            'guild_id': event.guild_id,
            'entity_id': event.entity_id,
            'name': event.name,
            'scheduled_start_time': str(int(event.start_time.timestamp())),
            'privacy_level': event.privacy_level.value,
            'status': event.status.value,
            'entity_type': 2,
            'channel_id': event.channel_id or 0,
            'entity_metadata': None,
        }
        if event.end_time:
            out["scheduled_end_time"] = str(int(event.end_time.timestamp()))
    else:
        out: _types.scheduled_event.ExternalScheduledEvent = {
            'id': event.id,
            'guild_id': event.guild_id,
            'entity_id': event.entity_id,
            'name': event.name,
            'scheduled_start_time': str(int(event.start_time.timestamp())),
            'privacy_level': event.privacy_level.value,
            'status': event.status.value,
            'entity_type': 3,
            'channel_id': None,
            'scheduled_end_time': str(int(event.end_time.timestamp())),
            'entity_metadata': {"location": event.location or ""}
        }
    return out


@dict_from_object.register(discord.Guild)
def _from_guild(guild: discord.Guild) -> _types.guild.Guild:
    return {
        'id': guild.id,
        'name': guild.name,
        'icon': guild.icon.url,
        'splash': guild.splash.url,
        'owner_id': guild.owner_id,
        'region': guild.region,
        'afk_channel_id': guild.afk_channel.id if guild.afk_channel else None,
        'afk_timeout': guild.afk_timeout,
        'verification_level': guild.verification_level.value,
        'default_message_notifications': guild.default_notifications.value,
        'explicit_content_filter': guild.explicit_content_filter.value,
        'roles': list(map(dict_from_object, guild.roles)),
        'emojis': list(map(dict_from_object, guild.emojis)),
        'features': guild.features,
        'mfa_level': guild.mfa_level.value,
        'application_id': None,
        'system_channel_id': guild.system_channel.id if guild.system_channel else None,
        'owner': guild.owner_id == guild.me.id,
        'discovery_splash': guild.discovery_splash.url if guild.discovery_splash else None,
        'stickers': list(map(dict_from_object, guild.stickers)),
        'banner': guild.banner.url if guild.banner else None,
        'description': guild.description,
        'incidents_data': guild._incidents_data,
        'nsfw_level': guild.nsfw_level.value,
        'system_channel_flags': guild.system_channel_flags.value,
        'rules_channel_id': guild.rules_channel.id if guild.rules_channel else None,
        'vanity_url_code': guild.vanity_url_code,
        'premium_tier': guild.premium_tier,
        'preferred_locale': guild.preferred_locale.value,
        'public_updates_channel_id': guild.public_updates_channel.id if guild.public_updates_channel else None,
        'stage_instances': list(map(dict_from_object, guild.stage_instances)),
        'guild_scheduled_events': list(map(dict_from_object, guild.scheduled_events)),
    }


# discord.py 1.7 bump requires the 'permissions_new', but if we keep 'permissions' then we seem to work on pre 1.7
def make_role_dict(
        name: str,
        id_num: int = -1,
        colour: int = 0,
        color: int | None = None,
        colors: _types.role.RoleColours | None = None,
        hoist: bool = False,
        position: int = -1,
        permissions: str = "104324161",
        managed: bool = False,
        mentionable: bool = False,
        flags: int = 0,
) -> _types.role.Role:
    if id_num < 0:
        id_num = make_id()
    if color is not None:
        if colour != 0:
            raise ValueError("Both 'colour' and 'color' can be supplied at the same time")
        colour = color
    if colors is None:
        colors: _types.role.RoleColours = {
            'primary_color': colour,
            'secondary_color': None,
            'tertiary_color': None,
        }
    return {
        'id': id_num,
        'name': name,
        'color': colour,
        'colors': colors,
        'hoist': hoist,
        'position': position,
        'permissions': permissions,
        'managed': managed,
        'mentionable': mentionable,
        'flags': flags,
    }


@typing.overload
def make_channel_dict(
        ctype: typing.Literal[0],
        id_num: int = ...,
        **kwargs: typing.Any,
) -> _types.channel.TextChannel: ...


@typing.overload
def make_channel_dict(
        ctype: typing.Literal[1],
        id_num: int = ...,
        **kwargs: typing.Any,
) -> _types.channel.DMChannel: ...


@typing.overload
def make_channel_dict(
        ctype: typing.Literal[2],
        id_num: int = ...,
        **kwargs: typing.Any,
) -> _types.channel.VoiceChannel: ...


@typing.overload
def make_channel_dict(
        ctype: typing.Literal[4],
        id_num: int = ...,
        **kwargs: typing.Any,
) -> _types.channel.CategoryChannel: ...


def make_channel_dict(ctype: typing.Literal[0, 1, 2, 3], id_num: int = -1,
                      **kwargs: typing.Any) -> _types.channel.PartialChannel:
    if id_num < 0:
        id_num = make_id()
    out: _types.channel.PartialChannel = {
        'id': id_num,
        'name': "",
        'type': ctype,
    }
    items = ("guild_id", "position", "permission_overwrites", "name", "topic", "nsfw", "last_message_id", "bitrate",
             "user_limit", "rate_limit_per_user", "recipients", "icon", "owner_id", "application_id", "parent_id",
             "last_pin_timestamp")
    _fill_optional(out, kwargs, items)
    return out


def make_text_channel_dict(name: str, id_num: int = -1, **kwargs: typing.Any) -> _types.channel.TextChannel:
    return make_channel_dict(discord.ChannelType.text.value, id_num, name=name, **kwargs)


def make_category_channel_dict(name: str, id_num: int = -1, **kwargs: typing.Any) -> _types.channel.CategoryChannel:
    return make_channel_dict(discord.ChannelType.category.value, id_num, name=name, **kwargs)


def make_dm_channel_dict(user: discord.User, id_num: int = -1, **kwargs: typing.Any) -> _types.channel.DMChannel:
    return make_channel_dict(discord.ChannelType.private.value, id_num, recipients=[dict_from_object(user)], **kwargs)


def make_voice_channel_dict(name: str, id_num: int = -1, **kwargs: typing.Any) -> _types.channel.VoiceChannel:
    return make_channel_dict(discord.ChannelType.voice.value, id_num, name=name, **kwargs)


def dict_from_overwrite(target: discord.Member | discord.Role,
                        overwrite: discord.PermissionOverwrite) -> _types.channel.PermissionOverwrite:
    allow, deny = overwrite.pair()
    ovr: _types.channel.PermissionOverwrite = {
        'id': target.id,
        'allow': str(allow.value),
        'deny': str(deny.value),
        'type': 0 if isinstance(target, discord.Role) else 1
    }
    return ovr


# TODO: Convert reactions, activity, and application to a dict.
def make_message_dict(
        channel: _types.AnyChannel,
        author: discord.user.BaseUser,
        id_num: int = -1,
        content: str = None,
        timestamp: str = None,
        edited_timestamp: str | None = None,
        tts: bool = False,
        mention_everyone: bool = False,
        mentions: list[discord.User | discord.Member] = None,
        mention_roles: list[int] = None,
        mention_channels: list[_types.AnyChannel] = None,
        attachments: list[discord.Attachment] = None,
        embeds: list[discord.Embed] | None = None,
        pinned: bool = False,
        type: int = 0,
        **kwargs,
) -> _types.message.Message:
    if mentions is None:
        mentions = []
    if mention_roles is None:
        mention_roles = []
    if mention_channels is None:
        mention_channels = []
    if attachments is None:
        attachments = []

    if not content:
        content = ""
    if id_num < 0:
        id_num = make_id()
    if isinstance(channel, discord.abc.GuildChannel):
        kwargs["guild_id"] = channel.guild.id
    if isinstance(author, discord.Member):
        author = author._user
        kwargs["member"] = dict_from_object(author)
    if timestamp is None:
        timestamp = str(int(discord.utils.snowflake_time(id_num).timestamp()))
    mentions = list(map(user_with_member, mentions)) if mentions else []
    mention_channels = list(map(_mention_from_channel, mention_channels)) if mention_channels else []
    attachments = list(map(dict_from_object, attachments)) if attachments else []
    embeds = list(map(discord.Embed.to_dict, embeds)) if embeds else []

    out: _types.message.Message = {
        'id': id_num,
        'channel_id': channel.id,
        'author': dict_from_object(author),
        'content': content,
        'timestamp': timestamp,
        'edited_timestamp': edited_timestamp,
        'tts': tts,
        'mention_channels': mention_channels,
        'mention_everyone': mention_everyone,
        'mentions': mentions,
        'mention_roles': mention_roles,
        'attachments': attachments,
        'embeds': embeds,
        'pinned': pinned,
        'type': type,
    }
    items = ('guild_id', 'member', 'reactions', 'nonce', 'webhook_id', 'activity', 'application')
    _fill_optional(out, kwargs, items)
    return out


def _mention_from_channel(channel: _types.AnyChannel) -> _types.message.ChannelMention:
    out: _types.message.ChannelMention = {
        "id": channel.id,
        "type": str(channel.type),
        "guild_id": 0,
        "name": ""
    }
    if hasattr(channel, "guild"):
        out["guild_id"] = channel.guild.id
    if hasattr(channel, "name"):
        out["name"] = channel.name

    return out


def _mention_from_role(role: discord.Role) -> int:
    return role.id


def make_attachment_dict(
        filename: str,
        size: int,
        url: str,
        proxy_url: str,
        id_num: int = -1,
        height: int | None = None,
        width: int | None = None,
        content_type: str = "txt"
) -> _types.message.Attachment:
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


def make_guild_dict(
        name: str,
        owner_id: int,
        roles: list[_types.role.Role],
        id_num: int = -1,
        emojis: list[_types.emoji.Emoji] | None = None,
        icon: str | None = None,
        splash: str | None = None,
        region: str = "en_north",
        afk_channel_id: int | None = None,
        afk_timeout: int = 600,
        verification_level: int = 0,
        default_message_notifications: int = 0,
        explicit_content_filter: int = 0,
        features: list[str] | None = None,
        mfa_level: int = 0,
        application_id: int | None = None,
        system_channel_id: int | None = None,
        **kwargs: typing.Any,
) -> _types.guild.Guild:
    if id_num < 0:
        id_num = make_id()
    if emojis is None:
        emojis = []
    if features is None:
        features = []
    out: _types.guild.Guild = {
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
        'discovery_splash': None,
        'stickers': [],
        'banner': None,
        'description': None,
        'incidents_data': None,
        'nsfw_level': 0,
        'system_channel_flags': 0,
        'rules_channel_id': None,
        'vanity_url_code': None,
        'premium_tier': 0,
        'preferred_locale': "en-US",
        'public_updates_channel_id': None,
        'stage_instances': [],
        'guild_scheduled_events': [],
    }
    items = ("owner", "permissions", "embed_enabled", "embed_channel_id", "widget_enabled", "widget_channel_id",
             "joined_at", "large", "unavailable", "member_count", "voice_states", "members", "channels", "presences")
    _fill_optional(out, kwargs, items)
    return out
