
from typing import Callable, Any, Coroutine, Optional


Callback = Callable[[Any, ...], Coroutine]


async def dispatch_event(event: str, *args: Any, **kwargs: Any) -> None: ...

def set_callback(cb: Callback, event: str) -> None: ...

def get_callback(event: str) -> Optional[Callback]: ...

def remove_callback(event: str) -> Optional[Callback]: ...
