
Getting Started
===============

Welcome to ``dpytest``, a python library for testing discord bots written using ``discord.py``. This tutorial
will explain how to install ``dpytest`` and set it up in your project, and write a simple test. If you already
know how to install libraries with pip, you probably want to skip to `Using Pytest`_.

Installing Dpytest
------------------

To start with, you should install dpytest with ``pip``. This will look a bit different, depending if you're
on Windows or Mac/Linux:

- Windows: ``py -m pip install dpytest``
- Linux: ``python3 -m pip install dpytest``

Using Dpytest
-------------

Once installed, you will need to import ``dpytest`` before you can use it. As it is an extension to ``discord.py``,
it goes into the ``discord.py`` extensions module. So, the most basic usage of dpytest would look like this:

.. code:: python

    import asyncio
    import discord.ext.test as dpytest


    async def test_ping():
        bot = ...  # However you create your bot.
        dpytest.configure(bot)
        await dpytest.message("!ping")
        assert dpytest.verify().message().contains().content("Ping:")
        await dpytest.empty_queue() # empty the global message queue as test teardown


    async def test_foo():
        bot = ... # Same setup as above
        dpytest.configure(bot)
        await dpytest.message("!hello")
        assert dpytest.verify().message().content("Hello World!")
        await dpytest.empty_queue() # empty the global message queue as test teardown


    asyncio.run(test_ping())
    asyncio.run(test_foo())

If that looks like a lot of code just to run tests, don't worry, there's a better way! We can use pytest,
a popular Python testing library.

--------------------

**Next Tutorial**: `Using Pytest`_

.. _Using Pytest: ./using_pytest.html
