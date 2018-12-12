
from typing import List, Dict, Iterable, Any, Union, Optional, Callable, Coroutine
import discord

JsonVals = Union[str, int, bool, Dict[str, 'JsonVals'], List['JsonVals']]
JsonDict = Dict[str, JsonVals]
Callback = Callable[[Any, ...], Coroutine]
AnyChannel = Union[discord.abc.GuildChannel, discord.abc.PrivateChannel]


#
# More internal, dict factories
#


def make_id() -> int: ...

def _fill_optional(data: JsonDict, obj: Any, items: Iterable[str]) -> None: ...

def make_user_dict(username: str, discrim: Union[str, int], avatar: Optional[str], id_num: int = ..., flags: int = ...,
                   bot: bool = ..., mfa_enabled: bool = ..., locale: str = ..., verified: bool = ..., email: str = ...,
                   premium_type: int = ...) -> JsonDict: ...

def dict_from_user(user: discord.User) -> JsonDict: ...

def make_member_dict(user: discord.User, roles: List[int], joined: int = ..., deaf: bool = ..., mute: bool = ...,
                     nick: str = ...) -> JsonDict: ...

def dict_from_member(member: discord.Member) -> JsonDict: ...

def make_role_dict(name: str, id_num: int = ..., colour: int = ..., hoist: bool = ..., position: int = ..., permissions: int = ...,
                   managed: bool = ..., mentionable: bool = ...) -> JsonDict: ...

def dict_from_role(role: discord.Role) -> JsonDict: ...

def make_channel_dict(ctype: int, id_num: int = ..., guild_id: int = ..., position: int = ..., permission_overwrites: JsonDict = ...,
                      name: str = ..., topic: Optional[str] = ..., nsfw: bool = ..., last_message_id: Optional[str] = ...,
                      bitrate: int = ..., user_limit: int = ..., rate_limit_per_user: int = ..., recipients: JsonDict = ...,
                      icon: Optional[str] = ..., owner_id: int = ..., application_id: int = ..., parent_id: Optional[int] = ...,
                      last_pin_timestamp: int = ...) -> JsonDict: ...

def make_text_channel_dict(name: str, id_num: int = ..., guild_id: int = ..., position: int = ..., permission_overwrites: JsonDict = ...,
                           topic: Optional[str] = ..., nsfw: bool = ..., last_message_id: Optional[int] = ...,
                           rate_limit_per_user: int = ..., parent_id: Optional[int]= ..., last_pin_timestamp: int = ...) -> JsonDict: ...

def dict_from_channel(channel: AnyChannel) -> JsonDict: ...

def make_message_dict(channel: AnyChannel, author: Union[discord.User, discord.Member], id_num: int = ..., content: str = ...,
                      timestamp: int = ..., edited_timestamp: Optional[int] = ..., tts: bool = ...,
                      mention_everyone: bool = ..., mentions: List[discord.User] = ..., mention_roles: List[int] = ...,
                      attachments: List[discord.Attachment] = ..., embeds: List[discord.Embed] = ..., pinned: bool = ...,
                      type: int = ..., guild_id: int = ..., member: discord.Member = ..., reactions: List[discord.Reaction] = ...,
                      nonce: Optional[int] = ..., webhook_id: int = ..., activity: discord.Activity = ..., application: JsonDict = ...): ...

# def dict_from_message(message: discord.Message) -> JsonDict: ...

def make_attachment_dict(filename: str, size: int, url: str, proxy_url: str, id_num: int = ..., height: Optional[int] = ...,
                         width: Optional[int] = ...) -> JsonDict: ...

def dict_from_attachment(attachment: discord.Attachment) -> JsonDict: ...

def make_guild_dict(name: str, owner_id: int, roles: List[JsonDict], id_num: int = ..., emojis: List[JsonDict] = ...,
                    icon: Optional[str] = ..., splash: Optional[str] = ..., region: str = ..., afk_channel_id: int = ...,
                    afk_timeout: int = ..., verification_level: int = ..., default_message_notifications: int = ...,
                    explicit_content_filter: int = ..., features: List[str] = ..., mfa_level: int = ..., application_id: int = ...,
                    system_channel_id: int = ..., owner: bool = ..., permissions: int = ..., embed_enabled: bool = ...,
                    embed_channel_id: int = ..., widget_enabled: bool = ..., widget_channel_id: int = ..., joined_at: int = ...,
                    large: bool = ..., unavailable: bool = ..., member_count: int = ..., voice_states: List[discord.VoiceState] = ...,
                    members: List[discord.Member] = ..., channels: List[discord.abc.GuildChannel] = ..., presences: List[discord.Activity] = ...) -> JsonDict: ...
