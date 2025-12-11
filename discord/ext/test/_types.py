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
AnyChannel = typing.Union[discord.TextChannel, discord.CategoryChannel,
discord.abc.GuildChannel, discord.abc.PrivateChannel]

if typing.TYPE_CHECKING:
    from discord.types import role, gateway
else:
    class OpenNamespace:
        def __getattr__(self, item: str) -> typing.Self:
            return self

        def __subclasscheck__(self, subclass: type) -> typing.Literal[True]:
            return True


    def __getattr__(name: str) -> OpenNamespace:
        return OpenNamespace()
