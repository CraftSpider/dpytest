"""
    Internal module for type-hinting aliases. Ensures single common definitions.
"""

import discord
import typing

T = typing.TypeVar('T')

JsonVal = str | int | bool | dict[str, 'JsonVal'] | list['JsonVal']
JsonDict = dict[str, JsonVal]
JsonList = list[JsonVal]
Callback = typing.Callable[..., typing.Coroutine[None, None, None]]
AnyChannel = discord.TextChannel | discord.CategoryChannel | discord.abc.GuildChannel | discord.abc.PrivateChannel

if typing.TYPE_CHECKING:
    # noqa: F401
    from discord.types import role, gateway
else:
    class OpenNamespace:
        def __getattr__(self, item: str) -> typing.Self:
            return self

        def __subclasscheck__(self, subclass: type) -> typing.Literal[True]:
            return True


    def __getattr__(name: str) -> OpenNamespace:
        return OpenNamespace()
