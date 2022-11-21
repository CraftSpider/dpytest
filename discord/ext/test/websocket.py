"""
    Mock implementation of a ``discord.gateway.DiscordWebSocket``. Overwrites a Client's default websocket, allowing
    hooking of its methods to update the backend and provide callbacks.
"""

import typing
import discord
import discord.gateway as gateway

from . import callbacks, _types


class FakeWebSocket(gateway.DiscordWebSocket):
    """
        A mock implementation of a ``DiscordWebSocket``. Instead of actually sending information to discord,
        it simply triggers calls to the ``dpytest`` backend, as well as triggering runner callbacks.
    """

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)
        self.cur_event = ""
        self.event_args = ()
        self.event_kwargs = {}

    async def send(self, data: _types.JsonDict) -> None:
        self._dispatch('socket_raw_send', data)
        if self.cur_event is None:
            raise ValueError("Unhandled Websocket send event")
        await callbacks.dispatch_event(self.cur_event, *self.event_args, **self.event_kwargs)
        self.cur_event = None
        self.event_args = ()
        self.event_kwargs = {}

    async def change_presence(
            self,
            *,
            activity: typing.Optional[discord.BaseActivity] = None,
            status: typing.Optional[str] = None,
            since: float = 0.0
    ) -> None:
        self.cur_event = "presence"
        self.event_args = (activity, status, since)
        await super().change_presence(activity=activity, status=status, since=since)
