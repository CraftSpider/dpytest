
import datetime as dt
import discord

generated_ids = 0


def make_id():
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


def _fill_optional(data, obj, items):
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


def make_user_dict(username, discrim, avatar, id_num=-1, flags=0, **kwargs):
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


def dict_from_user(user):
    out = {
        'id': user.id,
        'username': user.name,
        'discriminator': user.discriminator,
        'avatar': user.avatar
    }
    items = ("bot", "mfa_enabled", "locale", "verified", "email", "premium_type")
    _fill_optional(out, user, items)
    return out


def make_member_dict(guild, user, roles, joined=0, deaf=False, mute=False, **kwargs):
    out = {
        'guild_id': guild.id,
        'user': dict_from_user(user),
        'roles': roles,
        'joined_at': joined,
        'deaf': deaf,
        'mute': mute
    }
    items = ("nick",)
    _fill_optional(out, kwargs, items)
    return out


def dict_from_member(member):
    voice_state = member.voice
    #discord code adds default role to every member later on in Member constructor
    roles_no_default = list(filter(lambda r: not r == member.guild.default_role,member.roles))
    out = {
        'guild_id': member.guild.id,
        'user': dict_from_user(member._user),
        'roles': list(map(lambda role: int(role.id),roles_no_default)),
        'joined_at': member.joined_at,
    }
    if voice_state is not None:
        out['deaf'] = voice_state.deaf
        out['mute'] = voice_state.mute
    items = ("nick",)
    _fill_optional(out, member, items)
    return out


def make_role_dict(name, id_num=-1, colour=0, color=None, hoist=False, position=-1, permissions=104324161, managed=False,
                   mentionable=False):
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
        'permissions': permissions,
        'managed': managed,
        'mentionable': mentionable
    }


def dict_from_role(role):
    return {
        'id': role.id,
        'name': role.name,
        'color': role.colour.value,
        'hoist': role.hoist,
        'position': role.position,
        'permissions': role.permissions.value,
        'managed': role.managed,
        'mentionable': role.mentionable
    }


def make_channel_dict(ctype, id_num=-1, **kwargs):
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


def make_text_channel_dict(name, id_num=-1, **kwargs):
    return make_channel_dict(discord.ChannelType.text.value, id_num, name=name, **kwargs)

def make_category_channel_dict(name, id_num=-1, **kwargs):
    return make_channel_dict(discord.ChannelType.category.value, id_num, name=name, **kwargs )

def make_dm_channel_dict(user, id_num=-1, **kwargs):
    return make_channel_dict(discord.ChannelType.private, id_num, recipients=[dict_from_user(user)], **kwargs)


def dict_from_overwrite(target, overwrite):
    allow, deny = overwrite.pair()
    ovr = {
        'id': target.id,
        'allow': allow.value,
        'deny': deny.value
    }
    if isinstance(target, discord.Role):
        ovr['type'] = 'role'
    else:
        ovr['type'] = 'member'
    return ovr


# TODO: support all channel attributes
def dict_from_channel(channel):
    if isinstance(channel, discord.TextChannel):
        return {
            'name': channel.name,
            'position': channel.position,
            'id': channel.id,
            'guild_id': channel.guild.id,
            'permission_overwrites': [dict_from_overwrite(k, v) for k, v in channel.overwrites.items()],
            'type':channel.type,
            'parent_id':channel.category_id
        }
    if isinstance(channel,discord.CategoryChannel):
        return {
            'name': channel.name,
            'position': channel.position,
            'id': channel.id,
            'guild_id': channel.guild.id,
            'permission_overwrites': [dict_from_overwrite(k, v) for k, v in channel.overwrites.items()],
            'type': channel.type
        }


# TODO: Convert attachments, reactions, activity, and application to a dict.
def make_message_dict(channel, author, id_num=-1, content=None, timestamp=None, edited_timestamp=None, tts=False,
                      mention_everyone=False, mentions=None, mention_roles=None, mention_channels=None,
                      attachments=None, embeds=None, pinned=False, type=0, **kwargs):
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


def _mention_from_channel(channel):
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

def _mention_from_role(role):
    return role.id

def dict_from_message(message: discord.Message):
    out = {
        'id': message.id,
        'author': dict_from_user(message.author),
        'mentions': list(map(dict_from_user, message.mentions)),
        'mention_roles': list(map(_mention_from_role, message.role_mentions)),
        'mention_channels': list(map(_mention_from_channel, message.channel_mentions)),
        'edited_timestamp': message._edited_timestamp,
        'embeds' : list(map(discord.Embed.to_dict,message.embeds)),
        'attachments' : list(map(dict_from_attachment, message.attachments)),
    }

    items = ('content', 'pinned', 'application', 'activity', 'mention_everyone', 'tts', 'type', 
             'nonce')
    _fill_optional(out, message, items)
    return out


def make_attachment_dict(filename, size, url, proxy_url, id_num=-1, height=None, width=None):
    if id_num < 0:
        id_num = make_id()
    return {
        'id': id_num,
        'filename': filename,
        'size': size,
        'url': url,
        'proxy_url': proxy_url,
        'height': height,
        'width': width
    }


def dict_from_attachment(attachment):
    return {
        'id': attachment.id,
        'filename': attachment.filename,
        'size': attachment.size,
        'url': attachment.url,
        'proxy_url': attachment.proxy_url,
        'height': attachment.height,
        'width': attachment.width
    }


# TODO: dict_from_emoji and make_emoji_dict

def make_emoji_dict():
    pass


def dict_from_emoji(emoji):
    return {

    }


def make_guild_dict(name, owner_id, roles, id_num=-1, emojis=None, icon=None, splash=None, region="en_north",
                    afk_channel_id=None, afk_timeout=600, verification_level=0, default_message_notifications=0,
                    explicit_content_filter=0, features=None, mfa_level=0, application_id=None, system_channel_id=None,
                    **kwargs):
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


def dict_from_guild(guild):
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
