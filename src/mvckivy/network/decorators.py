from functools import wraps
from kivy.logger import Logger

from typing import Callable


def call_after(proc_after: Callable[..., None] | None):
    def decorator(proc_before: Callable[..., None]):
        @wraps(proc_before)
        def wrapper(*args, **kwargs) -> None:
            try:
                proc_before(*args, **kwargs)
            except Exception as ex:
                Logger.error(ex)
            finally:
                if proc_after:
                    proc_after(*args, **kwargs)
        return wrapper
    return decorator
