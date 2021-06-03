"""
    Mock implementation of a ``discord.state.ConnectionState``. Overwrites a Client's default state, allowing hooking of
    its methods and support for test-related features.
"""

import asyncio
import typing
import discord
import discord.http as dhttp
import discord.state as dstate

from . import factories as facts
from . import backend as back


class FakeState(dstate.ConnectionState):
    """
        A mock implementation of a ``ConnectionState``. Overrides methods that would otherwise cause issues, and
        implements functionality such as disabling dispatch temporarily.
    """

    http: 'back.FakeHttp'  # String because of circular import

    def __init__(self, client: discord.Client, http: dhttp.HTTPClient, user: discord.ClientUser = None, loop: asyncio.AbstractEventLoop = None) -> None:
        if loop is None:
            loop = asyncio.get_event_loop()
        super().__init__(dispatch=client.dispatch,
                         handlers=None, hooks=None,
                         syncer=None, http=http,
                         loop=loop, intents=client.intents,
                         member_cache_flags=client._connection.member_cache_flags)
        if user is None:
            user = discord.ClientUser(state=self, data=facts.make_user_dict("FakeApp", "0001", None))
            user.bot = True
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

    def stop_dispatch(self) -> None:
        """
            Stop dispatching events to the client, if we are
        """
        self._do_dispatch = False

    def start_dispatch(self) -> None:
        """
            Start dispatching events to the client, if we aren't already
        """
        self._do_dispatch = True

    # TODO: Respect limit parameters
    async def query_members(self, guild: discord.Guild, query: str, limit: int, user_ids: int, cache: bool, presences: bool) -> None:
        guild: discord.Guild = discord.utils.get(self.guilds, id=guild.id)
        return guild.members

    async def chunk_guild(self, guild: discord.Guild, *, wait: bool = True, cache: typing.Optional[bool] = None):
        pass

    def _guild_needs_chunking(self, guild: discord.Guild):
        """
        Prevents chunking which can throw asyncio wait_for errors with tests under 60 seconds
        """
        return False
