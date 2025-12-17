"""
    Internal module for type-hinting aliases. Ensures single common definitions.
"""
from enum import Enum
from typing import Callable, Coroutine, Literal, Self, TypeVar, Any, ParamSpec, Protocol
from mypy_extensions import VarArg, KwArg

import discord
import typing

if typing.TYPE_CHECKING:
    from discord.types import (
        role, gateway, appinfo, user, guild, emoji, channel, message, sticker,  # noqa: F401
        scheduled_event, member  # noqa: F401
    )

    AnyChannelJson = channel.VoiceChannel | channel.TextChannel | channel.DMChannel | channel.CategoryChannel
else:
    class OpenNamespace:
        def __getattr__(self, item: str) -> Self:
            return self

        def __subclasscheck__(self, subclass: type) -> Literal[True]:
            return True

        def __or__(self, other: T) -> T:
            return other

    def __getattr__(name: str) -> OpenNamespace:
        return OpenNamespace()

T = TypeVar('T')
P = ParamSpec('P')

Callback = Callable[..., Coroutine[None, None, None]]
AnyChannel = (discord.abc.GuildChannel | discord.TextChannel | discord.VoiceChannel | discord.StageChannel | discord.DMChannel | discord.Thread | discord.GroupChannel)


class Wrapper(Protocol[P, T]):
    __wrapped__: Callable[P, T]

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        ...


class FnWithOld(Protocol[P, T]):
    __old__: Callable[P, T] | None

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        ...


class Undef(Enum):
    undefined = None


undefined: Literal[Undef.undefined] = Undef.undefined
