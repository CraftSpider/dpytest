# dpytest

[![Build Status](https://travis-ci.com/CraftSpider/dpytest.svg?branch=master)](https://travis-ci.com/CraftSpider/dpytest)
[![Documentation Status](https://readthedocs.org/projects/dpytest/badge/?version=latest)](https://dpytest.readthedocs.io/en/latest/?badge=latest)


This is a package to allow testing of discord.py.
It is only compatible with the rewrite version, and is still in early alpha.
It relies on pytest-asyncio for asynchronous test running, as discord.py is coroutine driven.

# Documentation

Documentation can be found at [dpytest.readthedocs.io](https://dpytest.readthedocs.io/en/latest/), including examples and tutorials

# Usage

TODO: Move this to RTD

dpytest can be used for projects using the default commands.Bot, or those defining their own subclass of bot.
For someone using a custom class, code would look something like this:
```python
import discord.ext.test as dpytest
import yourbot
import pytest


@pytest.mark.asyncio
async def test_bot():
    bot = yourbot.BotClass()
    
    # Load any extensions/cogs you want to in here
    
    dpytest.configure(bot)
    
    await dpytest.message("!help")
    dpytest.verify_message("[Expected help output]")
```

The dpytest framework is designed to be used best with pytest style fixtures, but is technically framework agnostic.  
With pytest, the bot setup step would be moved into a fixture so each test could use that fixture. Configure will ensure
that all state is reset after each call.
