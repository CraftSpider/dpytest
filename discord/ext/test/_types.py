"""
    Internal module for type-hinting aliases. Ensures single common definitions.
"""

import discord
import typing

T = typing.TypeVar('T')

JsonVal = typing.Union[str, int, bool, typing.Dict[str, 'JsonVal'], typing.List['JsonVal']]
JsonDict = typing.Dict[str, JsonVal]
JsonList = typing.List[JsonVal]
Callback = typing.Callable[..., typing.Coroutine[None, None, None]]
AnyChannel = typing.Union[discord.TextChannel, discord.CategoryChannel, discord.abc.GuildChannel, discord.abc.PrivateChannel]
