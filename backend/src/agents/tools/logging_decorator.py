from __future__ import annotations

from functools import wraps
from typing import Callable, ParamSpec, TypeVar

from src.utils.logger import logger as log

P = ParamSpec("P")
R = TypeVar("R")


def log_tool_call(tool_name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Wrap a tool function with consistent start/success/error logs."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            log.info(f"Tool {tool_name} started")
            try:
                result = func(*args, **kwargs)
                log.info(f"Tool {tool_name} completed")
                return result
            except Exception as e:
                log.exception(f"Tool {tool_name} failed: {e}")
                raise

        return wrapper

    return decorator
