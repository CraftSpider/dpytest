
import asyncio
import discord
import discord.state as dstate
from . import factories as facts


class FakeState(dstate.ConnectionState):

    def __init__(self, client, http, user=None, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        super().__init__(dispatch=client.dispatch,
                         handlers=None, hooks=None,
                         syncer=None, http=http,
                         loop=loop)
        if user is None:
            user = discord.ClientUser(state=self, data=facts.make_user_dict("FakeApp", "0001", None))
        self.user = user
        self.shard_count = client.shard_count
        self._get_websocket = lambda x: client.ws
        self._do_dispatch = True

        real_disp = self.dispatch

        def dispatch(*args, **kwargs):
            if not self._do_dispatch:
                return
            return real_disp(*args, **kwargs)

        self.dispatch = dispatch

    def stop_dispatch(self):
        self._do_dispatch = False

    def start_dispatch(self):
        self._do_dispatch = True
