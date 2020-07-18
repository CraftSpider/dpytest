import logging


log = logging.getLogger("discord.ext.tests")


_callbacks = {}


async def dispatch_event(event, *args, **kwargs):
    cb = _callbacks.get(event)
    if cb is not None:
        try:
            await cb(*args, **kwargs)
        except Exception as e:
            log.error(f"Error in handler for event {event}: {e}")


def set_callback(cb, event):
    _callbacks[event] = cb


def get_callback(event):
    if _callbacks.get(event) is None:
        raise ValueError(f"Callback for event {event} not set")
    return _callbacks[event]


def remove_callback(event):
    return _callbacks.pop(event, None)
