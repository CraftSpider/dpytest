
import discord.gateway as gateway

from . import callbacks


class FakeWebSocket(gateway.DiscordWebSocket):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cur_event = ""
        self.event_args = ()
        self.event_kwargs = {}

    async def send(self, data):
        self._dispatch('socket_raw_send', data)
        if self.cur_event is None:
            raise ValueError("Unhandled Websocket send event")
        await callbacks.dispatch_event(self.cur_event, *self.event_args, **self.event_kwargs)
        self.cur_event = None
        self.event_args = ()
        self.event_kwargs = {}

    async def change_presence(self, *, activity=None, status=None, afk=False, since=0.0):
        self.cur_event = "presence"
        self.event_args = (activity, status, afk, since)
        await super().change_presence(activity=activity, status=status, afk=afk, since=since)
