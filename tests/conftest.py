from pathlib import Path
from typing import AsyncGenerator

import pytest_asyncio
import discord
import discord.ext.commands as commands
import discord.ext.test as dpytest
from pytest import FixtureRequest
from discord.client import _LoopSentinel


@pytest_asyncio.fixture
async def bot(request: FixtureRequest) -> commands.Bot:
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    b = commands.Bot(command_prefix="!",
                     intents=intents)
    # set up the loop
    if isinstance(b.loop, _LoopSentinel):
        await b._async_setup_hook()

    marks = request.function.pytestmark
    mark = None
    for mark in marks:
        if mark.name == "cogs":
            break

    if mark is not None:
        for extension in mark.args:
            await b.load_extension("tests.internal." + extension)

    dpytest.configure(b)
    return b


@pytest_asyncio.fixture(autouse=True)
async def cleanup() -> AsyncGenerator[None, None]:
    yield
    await dpytest.empty_queue()


def pytest_sessionfinish() -> None:
    """ Code to execute after all tests. """

    # dat files are created when using attachements
    print("\n-------------------------\nClean dpytest_*.dat files")
    file_list = Path('.').glob('dpytest_*.dat')
    for file_path in file_list:
        try:
            file_path.unlink()
        except Exception:
            print("Error while deleting file : ", file_path)
