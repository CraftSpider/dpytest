
from asyncio import AbstractEventLoop
from discord import Client, ClientUser
from discord.http import HTTPClient
from discord.state import ConnectionState
from .backend import FakeHttp

class FakeState(ConnectionState):

    http: FakeHttp

    def __init__(self, client: Client, http: HTTPClient, user: ClientUser = ..., loop: AbstractEventLoop = ...) -> None: ...

    def stop_dispatch(self) -> None: ...

    def start_dispatch(self) -> None: ...
