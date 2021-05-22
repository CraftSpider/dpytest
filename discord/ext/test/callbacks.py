"""
    Module containing registered callbacks for various events. These events are how various parts of discord.py
    can communicate with the frontend runner or a user's custom runner setup. These callbacks should not
    be used to trigger backend changes, that is the responsibility of the library internals.
"""

import logging
import typing
from . import _types


log = logging.getLogger("discord.ext.tests")


_callbacks = {}


async def dispatch_event(event: str, *args: typing.Any, **kwargs: typing.Any) -> None:
    cb = _callbacks.get(event)
    if cb is not None:
        try:
            await cb(*args, **kwargs)
        except Exception as e:
            log.error(f"Error in handler for event {event}: {e}")


def set_callback(cb: _types.Callback, event: str) -> None:
    _callbacks[event] = cb


def get_callback(event: str) -> _types.Callback:
    if _callbacks.get(event) is None:
        raise ValueError(f"Callback for event {event} not set")
    return _callbacks[event]


def remove_callback(event: str) -> typing.Optional[_types.Callback]:
    return _callbacks.pop(event, None)
