
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


    async def test_foo():
        bot = ... # Same setup as above
        dpytest.configure(bot)
        await dpytest.message("!hello")
        assert dpytest.verify().message().content("Hello World!")


    asyncio.run(test_ping())
    asyncio.run(test_foo())

One problem that could happen is that the ``sent_queue`` is shared between the tests. So in order not to mess between
your tests (``verify()`` pops **one** message from the queue, so in general, you won't need to do anything) you can
explicitly call ``empty_queue()``, as shown in the next example (and later, in the ``conftests.py``).

If that looks like a lot of code just to run tests, don't worry, there's a better way! We can use pytest,
a popular Python testing library.

--------------------

**Next Tutorial**: `Using Pytest`_

.. _Using Pytest: ./using_pytest.html
