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
    """
        Dispatch an event to a set handler, if one exists. Will ignore handler errors,
        just print a log

    :param event: Name of the event to dispatch
    :param args: Arguments to the callback
    :param kwargs: Keyword arguments to the callback
    """
    cb = _callbacks.get(event)
    if cb is not None:
        try:
            await cb(*args, **kwargs)
        except Exception as e:
            log.error(f"Error in handler for event {event}: {e}")


def set_callback(cb: _types.Callback, event: str) -> None:
    """
        Set the callback to use for a specific event

    :param cb: Callback to use
    :param event: Name of the event to register for
    """
    _callbacks[event] = cb


def get_callback(event: str) -> _types.Callback:
    """
        Get the current callback for an event, or raise an exception if one isn't set

    :param event: Event to get callback for
    :return: Callback for event, if one is set
    """
    if _callbacks.get(event) is None:
        raise ValueError(f"Callback for event {event} not set")
    return _callbacks[event]


def remove_callback(event: str) -> typing.Optional[_types.Callback]:
    """
        Remove the callback set for an event, returning it, or None if one isn't set

    :param event: Event to remove callback for
    :return: Callback that was previously set or None
    """
    return _callbacks.pop(event, None)
