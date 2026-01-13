"""
    Internal module for type-hinting aliases. Ensures single common definitions.
"""
from enum import Enum
import typing
from typing import Callable, Literal, Self, TypeVar, ParamSpec, Protocol

import discord

T = TypeVar('T')
P = ParamSpec('P')

AnyChannel = (discord.abc.GuildChannel | discord.TextChannel | discord.VoiceChannel | discord.StageChannel
              | discord.DMChannel | discord.Thread | discord.GroupChannel)


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


if typing.TYPE_CHECKING:
    from discord.types import (
        role as role, gateway as gateway, appinfo as appinfo, user as user, guild as guild,  # noqa: F401
        emoji as emoji, channel as channel, message as message, sticker as sticker,  # noqa: F401
        snowflake as snowflake, scheduled_event as scheduled_event, member as member, poll as poll  # noqa: F401
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
