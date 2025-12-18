"""
    Module containing registered callbacks for various events. These events are how various parts of discord.py
    can communicate with the frontend runner or a user's custom runner setup. These callbacks should not
    be used to trigger backend changes, that is the responsibility of the library internals.
"""

import logging
import typing
import discord
from enum import Enum
from typing import Callable, overload, Literal, Any, Awaitable

from . import _types

GetChannelCallback = Callable[[_types.snowflake.Snowflake], Awaitable[None]]
SendMessageCallback = Callable[[discord.Message], Awaitable[None]]
EditMemberCallback = Callable[[dict[str, Any], discord.Member, str | None], Awaitable[None]]
Callback = GetChannelCallback | SendMessageCallback | EditMemberCallback | Callable[..., Awaitable[None]]

log = logging.getLogger("discord.ext.tests")


class CallbackEvent(Enum):
    get_channel = "get_channel"
    presence = "presence"
    start_private_message = "start_private_message"
    send_message = "send_message"
    send_typing = "send_typing"
    delete_message = "delete_message"
    edit_message = "edit_message"
    add_reaction = "add_reaction"
    remove_reaction = "remove_reaction"
    remove_own_reaction = "remove_own_reaction"
    get_message = "get_message"
    logs_from = "logs_from"
    kick = "kick"
    ban = "ban"
    unban = "unban"
    change_nickname = "change_nickname"
    edit_member = "edit_member"
    create_role = "create_role"
    edit_role = "edit_role"
    delete_role = "delete_role"
    move_role = "move_role"
    add_role = "add_role"
    remove_role = "remove_role"
    app_info = "app_info"
    get_guilds = "get_guilds"


_callbacks: dict[CallbackEvent, Callback] = {}


async def dispatch_event(event: CallbackEvent, *args: typing.Any, **kwargs: typing.Any) -> None:
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


@overload
def set_callback(cb: GetChannelCallback, event: Literal[CallbackEvent.get_channel]) -> None: ...


@overload
def set_callback(cb: SendMessageCallback, event: Literal[CallbackEvent.send_message]) -> None: ...


@overload
def set_callback(cb: EditMemberCallback, event: Literal[CallbackEvent.edit_member]) -> None: ...


def set_callback(cb: Callback, event: CallbackEvent) -> None:
    """
        Set the callback to use for a specific event

    :param cb: Callback to use
    :param event: Name of the event to register for
    """
    _callbacks[event] = cb


def get_callback(event: CallbackEvent) -> Callback:
    """
        Get the current callback for an event, or raise an exception if one isn't set

    :param event: Event to get callback for
    :return: Callback for event, if one is set
    """
    if _callbacks.get(event) is None:
        raise ValueError(f"Callback for event {event} not set")
    return _callbacks[event]


def remove_callback(event: CallbackEvent) -> Callback | None:
    """
        Remove the callback set for an event, returning it, or None if one isn't set

    :param event: Event to remove callback for
    :return: Callback that was previously set or None
    """
    return _callbacks.pop(event, None)
