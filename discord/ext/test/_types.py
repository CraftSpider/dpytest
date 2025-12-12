"""
    Internal module for type-hinting aliases. Ensures single common definitions.
"""

import discord
import typing

T = typing.TypeVar('T')

Callback = typing.Callable[..., typing.Coroutine[None, None, None]]
AnyChannel = discord.TextChannel | discord.CategoryChannel | discord.abc.GuildChannel | discord.abc.PrivateChannel | discord.Thread

if typing.TYPE_CHECKING:
    # noqa: F401
    from discord.types import role, gateway, appinfo, user, guild, emoji, channel, message, sticker, scheduled_event, \
        member

    AnyChannelJson = channel.VoiceChannel | channel.TextChannel | channel.DMChannel | channel.CategoryChannel
else:
    class OpenNamespace:
        def __getattr__(self, item: str) -> typing.Self:
            return self

        def __subclasscheck__(self, subclass: type) -> typing.Literal[True]:
            return True

        def __or__(self, other):
            return other


    def __getattr__(name: str) -> OpenNamespace:
        return OpenNamespace()
