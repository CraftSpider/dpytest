from typing import Callable

from discord import Client, VoiceClient
from discord.abc import Connectable, T
from discord.channel import VoiceChannel


class FakeVoiceClient(VoiceClient):
    """
    Mock implementation of a Discord VoiceClient. VoiceClient.connect tries to contact the Discord API and is called
    whenever connect() is called on a VoiceChannel, so we need to override that method and pass in the fake version
    to prevent the program from actually making calls to the Discord API.
    """

    async def connect(self, *, reconnect: bool, timeout: float, self_deaf: bool = False,
                      self_mute: bool = False) -> None:
        self._connection._connected.set()


class FakeVoiceChannel(VoiceChannel):
    """
    Mock implementation of a Discord VoiceChannel. Exists just to pass a FakeVoiceClient into the superclass connect()
    method.
    """

    async def connect(
            self,
            *,
            timeout: float = 60.0,
            reconnect: bool = True,
            cls: Callable[[Client, Connectable], T] = FakeVoiceClient,  # type: ignore[assignment]
            self_deaf: bool = False,
            self_mute: bool = False,
    ) -> T:
        return await super().connect(timeout=timeout, reconnect=reconnect, cls=cls, self_deaf=self_deaf,
                                     self_mute=self_mute)
