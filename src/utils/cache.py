from functools import wraps
from typing import Callable, Any, Dict, Tuple

def memoize(func: Callable[..., Any]) -> Callable[..., Any]:
    cache: Dict[Tuple, Any] = {}

    @wraps(func)
    def wrapper(*args, **kwargs):
        key = (args, tuple(sorted(kwargs.items())))
        if key in cache:
            return cache[key]
        result = func(*args, **kwargs)
        cache[key] = result
        return result

    return wrapper
