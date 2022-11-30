import glob
import os
import pytest_asyncio
import discord
import discord.ext.commands as commands
import discord.ext.test as dpytest
from discord.client import _LoopSentinel


@pytest_asyncio.fixture
async def bot(request):
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
async def cleanup():
    yield
    await dpytest.empty_queue()


def pytest_sessionfinish(session, exitstatus):
    """ Code to execute after all tests. """

    # dat files are created when using attachements
    print("\n-------------------------\nClean dpytest_*.dat files")
    fileList = glob.glob('./dpytest_*.dat')
    for filePath in fileList:
        try:
            os.remove(filePath)
        except Exception:
            print("Error while deleting file : ", filePath)
