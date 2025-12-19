"""
    Module for (mostly) stateless creation/destructuring of discord.py objects. Primarily a utility
    for the rest of the library, which often needs to convert between objects and JSON at various stages.
"""
import functools
import datetime as dt
from typing import Any, Literal, overload, Iterable, Protocol, NoReturn, Callable, ParamSpec, TypeVar

import discord
from . import _types


P = ParamSpec('P')
T = TypeVar('T')

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


@overload
def _fill_optional(
        data: _types.user.User,
        obj: discord.user.BaseUser | dict[str, object],
        items: Iterable[str]
) -> None: ...


@overload
def _fill_optional(
        data: _types.member.Member | _types.member.MemberWithUser,
        obj: discord.Member | dict[str, object],
        items: Iterable[str]
) -> None: ...


@overload
def _fill_optional(
        data: _types.gateway.GuildMemberUpdateEvent,
        obj: discord.Member | dict[str, object],
        items: Iterable[str]
) -> None: ...


@overload
def _fill_optional(
        data: _types.guild.Guild,
        obj: discord.Guild | dict[str, object],
        items: Iterable[str]
) -> None: ...


@overload
def _fill_optional(
        data: _types.channel.PartialChannel,
        obj: _types.AnyChannel | dict[str, object],
        items: Iterable[str]
) -> None: ...


@overload
def _fill_optional(
        data: _types.message.Message,
        obj: discord.Message | dict[str, object],
        items: Iterable[str]
) -> None: ...


@overload
def _fill_optional(
        data: _types.emoji.Emoji,
        obj: discord.Emoji | dict[str, object],
        items: Iterable[str]
) -> None: ...


@overload
def _fill_optional(
        data: _types.sticker.GuildSticker,
        obj: discord.GuildSticker | dict[str, object],
        items: Iterable[str]
) -> None: ...


def _fill_optional(  # type: ignore[misc]
        data: dict[str, object],
        obj: object | dict[str, object],
        items: Iterable[str]
) -> None:
    if isinstance(obj, dict):
        _fill_optional_dict(data, obj, items)
    else:
        _fill_optional_value(data, obj, items)


def _fill_optional_dict(
        data: dict[str, object],
        obj: dict[str, object],
        items: Iterable[str],
) -> None:
    for item in items:
        result = obj.pop(item, None)
        if result is None:
            continue
        data[item] = result
    if len(obj) > 0:
        print("Warning: Invalid attributes passed")


def _fill_optional_value(
        data: dict[str, object],
        obj: object,
        items: Iterable[str],
) -> None:
    for item in items:
        if item == "permissions":
            print()
        if (val := getattr(obj, item, None)) is None and (val := getattr(obj, f"_{item}", None)) is None:
            continue
        data[item] = val


def make_user_dict(username: str, discrim: str | int, avatar: str | None, id_num: int = -1, flags: int = 0,
                   **kwargs: Any) -> _types.user.User:
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
    items = ("bot", "system", "mfa_enabled", "locale", "verified", "email", "premium_type", "public_flags")
    _fill_optional(out, kwargs, items)
    return out


def make_member_dict(
        user: discord.user.BaseUser,
        roles: list[_types.gateway.Snowflake],
        joined: str | None = None,
        deaf: bool = False,
        mute: bool = False,
        flags: int = 0,
        **kwargs: Any,
) -> _types.member.MemberWithUser:
    out: _types.member.MemberWithUser = {
        'user': dict_from_object(user),
        'roles': roles,
        'joined_at': joined,
        'deaf': deaf,
        'mute': mute,
        'flags': flags,
    }
    items = ("avatar", "nick", "premium_since", "pending", "permissions", "communication_disabled_until", "avatar_decoration_data")
    _fill_optional(out, kwargs, items)
    return out


def user_with_member(user: discord.User | discord.Member) -> _types.member.UserWithMember:
    if isinstance(user, discord.Member):
        member: _types.member.MemberWithUser | None = dict_from_object(user)
        user = user._user
    else:
        member = None
    out: _types.member.UserWithMember = dict_from_object(user)
    if member:
        out['member'] = member
    return out


class DictFromObject(Protocol):
    @overload
    def __call__(self, obj: discord.user.BaseUser) -> _types.member.UserWithMember: ...
    @overload
    def __call__(self, obj: discord.Member, *, guild: Literal[False] = ...) -> _types.member.MemberWithUser: ...
    @overload
    def __call__(self, obj: discord.Member, *, guild: Literal[True] = ...) -> _types.gateway.GuildMemberUpdateEvent: ...
    @overload
    def __call__(self, obj: discord.Member, *, guild: bool = ...) -> _types.member.MemberWithUser | _types.gateway.GuildMemberUpdateEvent: ...
    @overload
    def __call__(self, obj: discord.Role) -> _types.role.Role: ...

    @overload
    def __call__(self, obj: discord.TextChannel) -> _types.channel.TextChannel: ...
    @overload
    def __call__(self, obj: discord.DMChannel) -> _types.channel.DMChannel: ...
    @overload
    def __call__(self, obj: discord.CategoryChannel) -> _types.channel.CategoryChannel: ...
    @overload
    def __call__(self, obj: discord.VoiceChannel) -> _types.channel.VoiceChannel: ...
    @overload
    def __call__(self, obj: _types.AnyChannel) -> _types.channel.Channel: ...

    @overload
    def __call__(self, obj: discord.Message) -> _types.message.Message: ...
    @overload
    def __call__(self, obj: discord.Attachment) -> _types.message.Attachment: ...
    @overload
    def __call__(self, obj: discord.Emoji) -> _types.emoji.Emoji: ...

    @overload
    def __call__(self, obj: discord.GuildSticker) -> _types.sticker.GuildSticker: ...
    @overload
    def __call__(self, obj: discord.Sticker) -> _types.sticker.Sticker: ...

    @overload
    def __call__(self, obj: discord.StageInstance) -> _types.guild.StageInstance: ...
    @overload
    def __call__(self, obj: discord.ScheduledEvent) -> _types.guild.GuildScheduledEvent: ...
    @overload
    def __call__(self, obj: discord.Guild) -> _types.guild.Guild: ...

    @overload
    def __call__(
            self,
            obj: discord.PermissionOverwrite,
            *,
            target: discord.Member | discord.Role | discord.Object,
    ) -> _types.channel.PermissionOverwrite: ...

    def __call__(self, obj: object, **_kwargs: Any) -> NoReturn: ...

    def register(self, ty: type) -> Callable[[Callable[P, T]], Callable[P, T]]: ...


dict_from_object: DictFromObject


@functools.singledispatch  # type: ignore[no-redef]
def dict_from_object(obj: object, **_kwargs: Any) -> Any:
    raise TypeError(f"Unrecognized discord model type {type(obj)}")


@dict_from_object.register(discord.user.BaseUser)
def _from_base_user(user: discord.user.BaseUser) -> _types.member.UserWithMember:
    out: _types.member.UserWithMember = {
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
def _from_member(member: discord.Member, *, guild: bool = False) -> _types.member.MemberWithUser | _types.gateway.GuildMemberUpdateEvent:
    # discord code adds default role to every member later on in Member constructor
    roles_no_default = list(filter(lambda r: not r == member.guild.default_role, member.roles))
    items: tuple[str, ...]
    if guild:
        out: _types.gateway.GuildMemberUpdateEvent = {
            'guild_id': member.guild.id,
            'user': dict_from_object(member._user),
            'avatar': member.avatar.url if member.avatar else "",
            'roles': list(map(lambda role: int(role.id), roles_no_default)),
            'joined_at': str(int(member.joined_at.timestamp())) if member.joined_at else None,
            'flags': member.flags.value,
            'deaf': member.voice.deaf if member.voice else False,
            'mute': member.voice.mute if member.voice else False,
        }
        items = ("nick", "premium_since", "pending", "permissions", "communication_disabled_until", "avatar_decoration_data")
        _fill_optional(out, member, items)
        return out
    else:
        mem_user: _types.member.MemberWithUser = {
            'user': dict_from_object(member._user),
            'roles': list(map(lambda role: int(role.id), roles_no_default)),
            'joined_at': str(int(member.joined_at.timestamp())) if member.joined_at else None,
            'flags': member.flags.value,
            'deaf': member.voice.deaf if member.voice else False,
            'mute': member.voice.mute if member.voice else False,
        }
        items = ("avatar", "nick", "premium_since", "pending", "permissions", "communication_disabled_until", "avatar_decoration_data")
        _fill_optional(mem_user, member, items)
        return mem_user


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
        'permission_overwrites': [dict_from_object(v, target=k) for k, v in channel.overwrites.items()],
        'type': channel.type.value,
        'parent_id': channel.category_id,
        'nsfw': channel.nsfw,
    }


@dict_from_object.register(discord.DMChannel)
def _from_dm_channel(channel: discord.DMChannel) -> _types.channel.DMChannel:
    return {
        'id': channel.id,
        'name': "",
        'type': channel.type.value,
        # TODO: Map this correctly?
        'last_message_id': 0,
        'recipients': list(map(dict_from_object, channel.recipients))
    }


@dict_from_object.register(discord.CategoryChannel)
def _from_category_channel(channel: discord.CategoryChannel) -> _types.channel.CategoryChannel:
    return {
        'name': channel.name,
        'position': channel.position,
        'id': channel.id,
        'guild_id': channel.guild.id,
        'permission_overwrites': [dict_from_object(v, target=k) for k, v in channel.overwrites.items()],
        'type': channel.type.value,
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
        'permission_overwrites': [dict_from_object(v, target=k) for k, v in channel.overwrites.items()],
        'type': channel.type.value,
        'nsfw': channel.nsfw,
        'parent_id': channel.category_id,
        'bitrate': channel.bitrate,
        'user_limit': channel.user_limit,
    }


@dict_from_object.register(discord.Message)
def _from_message(message: discord.Message) -> _types.message.Message:
    if isinstance(message.author, discord.Member):
        member: _types.member.MemberWithUser | None = dict_from_object(message.author)
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
        'type': message.type.value,  # type: ignore[typeddict-item]
    }
    if member:
        out['member'] = {**member}

    items = ('content', 'pinned', 'activity',
             'mention_everyone', 'tts', 'type', 'nonce')
    _fill_optional(out, message, items)
    return out


@dict_from_object.register(discord.Attachment)
def _from_attachment(attachment: discord.Attachment) -> _types.message.Attachment:
    out: _types.message.Attachment = {
        'id': attachment.id,
        'filename': attachment.filename,
        'size': attachment.size,
        'url': attachment.url,
        'proxy_url': attachment.proxy_url,
        'height': attachment.height,
        'width': attachment.width,
    }
    if attachment.content_type:
        out['content_type'] = attachment.content_type
    return out


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
        standard: _types.sticker.StandardSticker = {
            'id': sticker.id,
            'name': sticker.name,
            'description': sticker.description,
            'tags': ",".join(sticker.tags),
            'format_type': sticker.format.value,
            'type': 1,
            'sort_value': sticker.sort_value,
            'pack_id': sticker.pack_id,
        }
        return standard
    elif isinstance(sticker, discord.GuildSticker):
        guild: _types.sticker.GuildSticker = {
            'id': sticker.id,
            'name': sticker.name,
            'description': sticker.description,
            'tags': sticker.emoji,
            'format_type': sticker.format.value,
            'type': 2,
            'available': sticker.available,
            'guild_id': sticker.guild_id,
        }
        items = ("user",)
        _fill_optional(guild, sticker, items)
        return guild
    else:
        raise TypeError(f"Invalid type for sticker {type(sticker)}")


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
        stage: _types.scheduled_event.StageInstanceScheduledEvent = {
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
            stage["scheduled_end_time"] = str(int(event.end_time.timestamp()))
        return stage
    elif event.entity_type == discord.EntityType.voice:
        voice: _types.scheduled_event.VoiceScheduledEvent = {
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
            voice["scheduled_end_time"] = str(int(event.end_time.timestamp()))
        return voice
    else:
        external: _types.scheduled_event.ExternalScheduledEvent = {
            'id': event.id,
            'guild_id': event.guild_id,
            'entity_id': event.entity_id,
            'name': event.name,
            'scheduled_start_time': str(int(event.start_time.timestamp())),
            'privacy_level': event.privacy_level.value,
            'status': event.status.value,
            'entity_type': 3,
            'channel_id': None,
            # end_time guaranteed non-None for external events
            'scheduled_end_time': str(int(event.end_time.timestamp())),  # type: ignore[union-attr]
            'entity_metadata': {"location": event.location or ""}
        }
        return external


@dict_from_object.register(discord.Guild)
def _from_guild(guild: discord.Guild) -> _types.guild.Guild:
    return {
        'id': guild.id,
        'name': guild.name,
        'icon': guild.icon.url if guild.icon else None,
        'splash': guild.splash.url if guild.splash else None,
        'owner_id': guild.owner_id or 0,
        'region': "us-west",  # deprecated?
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
        'premium_tier': guild.premium_tier,  # type: ignore[typeddict-item]
        'preferred_locale': guild.preferred_locale.value,
        'public_updates_channel_id': guild.public_updates_channel.id if guild.public_updates_channel else None,
        'stage_instances': list(map(dict_from_object, guild.stage_instances)),
        'guild_scheduled_events': list(map(dict_from_object, guild.scheduled_events)),
    }


@dict_from_object.register(discord.PermissionOverwrite)
def _from_overwrite(
        overwrite: discord.PermissionOverwrite,
        *,
        target: discord.Member | discord.Role | discord.Object,
) -> _types.channel.PermissionOverwrite:
    allow, deny = overwrite.pair()
    ovr: _types.channel.PermissionOverwrite = {
        'id': target.id,
        'allow': str(allow.value),
        'deny': str(deny.value),
        'type': 0 if isinstance(target, discord.Role) else 1
    }
    return ovr


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
        colors = {
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


@overload
def make_channel_dict(
        ctype: Literal[0],
        id_num: int = ...,
        **kwargs: Any,
) -> _types.channel.TextChannel: ...


@overload
def make_channel_dict(
        ctype: Literal[1],
        id_num: int = ...,
        **kwargs: Any,
) -> _types.channel.DMChannel: ...


@overload
def make_channel_dict(
        ctype: Literal[2],
        id_num: int = ...,
        **kwargs: Any,
) -> _types.channel.VoiceChannel: ...


@overload
def make_channel_dict(
        ctype: Literal[4],
        id_num: int = ...,
        **kwargs: Any,
) -> _types.channel.CategoryChannel: ...


def make_channel_dict(
        ctype: Literal[0, 1, 2, 3, 4],
        id_num: int = -1,
        **kwargs: Any,
) -> _types.channel.Channel:
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
    return out  # type: ignore[return-value]


def make_text_channel_dict(name: str, id_num: int = -1, **kwargs: Any) -> _types.channel.TextChannel:
    return make_channel_dict(discord.ChannelType.text.value, id_num, name=name, **kwargs)


def make_category_channel_dict(name: str, id_num: int = -1, **kwargs: Any) -> _types.channel.CategoryChannel:
    return make_channel_dict(discord.ChannelType.category.value, id_num, name=name, **kwargs)


def make_dm_channel_dict(user: discord.User, id_num: int = -1, **kwargs: Any) -> _types.channel.DMChannel:
    return make_channel_dict(discord.ChannelType.private.value, id_num, recipients=[dict_from_object(user)], **kwargs)


def make_voice_channel_dict(name: str, id_num: int = -1, **kwargs: Any) -> _types.channel.VoiceChannel:
    return make_channel_dict(discord.ChannelType.voice.value, id_num, name=name, **kwargs)


# TODO: Convert reactions, activity, and application to a dict.
def make_message_dict(
        channel: _types.AnyChannel,
        author: discord.user.BaseUser | discord.Member,
        id_num: int = -1,
        content: str = "",
        timestamp: str | None = None,
        edited_timestamp: str | None = None,
        tts: bool = False,
        mention_everyone: bool = False,
        mentions: list[discord.User | discord.Member] | None = None,
        mention_roles: list[_types.gateway.Snowflake] | None = None,
        mention_channels: list[_types.AnyChannel] | None = None,
        attachments: list[discord.Attachment] | None = None,
        embeds: list[discord.Embed] | None = None,
        pinned: bool = False,
        type: int = 0,
        **kwargs: Any,
) -> _types.message.Message:
    if mentions is None:
        mentions = []
    if mention_roles is None:
        mention_roles = []
    if mention_channels is None:
        mention_channels = []
    if attachments is None:
        attachments = []

    if id_num < 0:
        id_num = make_id()
    if isinstance(channel, discord.abc.GuildChannel):
        kwargs["guild_id"] = channel.guild.id
    if isinstance(author, discord.Member):
        author = author._user
        kwargs["member"] = dict_from_object(author)
    if timestamp is None:
        timestamp = str(int(discord.utils.snowflake_time(id_num).timestamp()))
    mentions_json = list(map(user_with_member, mentions)) if mentions else []
    mention_channels_json = list(map(_mention_from_channel, mention_channels)) if mention_channels else []
    attachments_json = list(map(dict_from_object, attachments)) if attachments else []
    embeds_json = list(map(discord.Embed.to_dict, embeds)) if embeds else []

    out: _types.message.Message = {
        'id': id_num,
        'channel_id': channel.id,
        'author': dict_from_object(author),
        'content': content,
        'timestamp': timestamp,
        'edited_timestamp': edited_timestamp,
        'tts': tts,
        'mention_channels': mention_channels_json,
        'mention_everyone': mention_everyone,
        'mentions': mentions_json,
        'mention_roles': mention_roles,
        'attachments': attachments_json,
        'embeds': embeds_json,
        'pinned': pinned,
        'type': type,  # type: ignore[typeddict-item]
    }
    items = ('guild_id', 'member', 'reactions', 'nonce', 'webhook_id', 'activity', 'application')
    _fill_optional(out, kwargs, items)
    return out


def _mention_from_channel(channel: _types.AnyChannel) -> _types.message.ChannelMention:
    out: _types.message.ChannelMention = {
        "id": channel.id,
        "type": channel.type.value,
        "guild_id": 0,
        "name": ""
    }
    if hasattr(channel, "guild"):
        out["guild_id"] = channel.guild.id if channel.guild else 0
    if hasattr(channel, "name"):
        out["name"] = channel.name or "<unknown name>"

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
        verification_level: Literal[0, 1, 2, 3, 4] = 0,
        default_message_notifications: Literal[0, 1] = 0,
        explicit_content_filter: Literal[0, 1, 2] = 0,
        features: list[_types.guild.GuildFeature] | None = None,
        mfa_level: Literal[0, 1] = 0,
        application_id: int | None = None,
        system_channel_id: int | None = None,
        **kwargs: Any,
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
