"""
    Mock implementation of a ``discord.state.ConnectionState``. Overwrites a Client's default state, allowing hooking of
    its methods and support for test-related features.
"""

import asyncio
import discord
import discord.http as dhttp
import discord.state as dstate

from . import factories as facts
from . import backend as back
from .voice import FakeVoiceChannel


class FakeState(dstate.ConnectionState):
    """
        A mock implementation of a ``ConnectionState``. Overrides methods that would otherwise cause issues, and
        implements functionality such as disabling dispatch temporarily.
    """

    http: 'back.FakeHttp'  # String because of circular import
    user: discord.ClientUser

    def __init__(self, client: discord.Client, http: dhttp.HTTPClient, user: discord.ClientUser | None = None,
                 loop: asyncio.AbstractEventLoop | None = None) -> None:
        if loop is None:
            loop = asyncio.get_event_loop()
        super().__init__(dispatch=client.dispatch,
                         handlers={}, hooks={},
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
        self._get_client = lambda: client

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
    async def query_members(self, guild: discord.Guild, query: str | None, limit: int, user_ids: list[int] | None,
                            cache: bool, presences: bool) -> list[discord.Member]:
        guild = discord.utils.get(self.guilds, id=guild.id)  # type: ignore[assignment]
        return list(guild.members)

    async def chunk_guild(self, guild: discord.Guild, *, wait: bool = True, cache: bool | None = None):
        pass

    def _guild_needs_chunking(self, guild: discord.Guild):
        """
        Prevents chunking which can throw asyncio wait_for errors with tests under 60 seconds
        """
        return False

    def parse_channel_create(self, data) -> None:
        """
        Need to make sure that FakeVoiceChannels are created when this is called to create VoiceChannels. Otherwise,
        guilds would not be set up correctly.

        :param data: info to use in channel creation.
        """
        if data['type'] == discord.ChannelType.voice.value:
            factory, ch_type = FakeVoiceChannel, discord.ChannelType.voice.value
        else:
            factory, ch_type = discord.channel._channel_factory(data['type'])

        if factory is None:
            return

        guild_id = discord.utils._get_as_snowflake(data, 'guild_id')
        guild = self._get_guild(guild_id)
        if guild is not None:
            # the factory can't be a DMChannel or GroupChannel here
            channel = factory(guild=guild, state=self, data=data)  # type: ignore
            guild._add_channel(channel)  # type: ignore
            self.dispatch('guild_channel_create', channel)
        else:
            return
