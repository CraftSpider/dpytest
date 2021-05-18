"""
    Aliases purely for type hinting of files
"""

import discord
import typing

JsonVals = typing.Union[str, int, bool, 'JsonDict', 'JsonList']
JsonDict = typing.Dict[str, JsonVals]
JsonList = typing.List[JsonVals]
Callback = typing.Callable[[typing.Any, ...], typing.Coroutine[None]]
AnyChannel = typing.Union[discord.TextChannel, discord.CategoryChannel, discord.abc.GuildChannel, discord.abc.PrivateChannel]
