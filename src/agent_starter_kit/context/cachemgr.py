from functools import wraps
import os
from hashlib import sha256
import json
from typing import Any, Callable, TypeVar, Optional, Protocol, ParamSpec, cast
from dataclasses import dataclass
from datetime import datetime
from collections.abc import Callable

class CacheInterface(Protocol):
    def get(self, key: str) -> Optional[Any]: ...
    def set(self, key: str, value: Any, args: tuple | None = None, kwargs: dict | None = None) -> None: ...


@dataclass
class CacheEntry:
    result: Any
    args: Any
    kwargs: Any
    cached_at: str = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            'result': self.result,
            'args': self.args,
            'kwargs': self.kwargs,
            'cached_at': self.cached_at
        }


class CacheManager:
    """
    Generic cache manager for function results
    
    It stores the results in JSON files in the cache directory.
    """

    def __init__(self, cache_dir: str = "cache", save_input: bool = True) -> None:
        """
        Initialize the cache manager
        
        Args:
            cache_dir (str): The directory to store the cache files. default: "cache"
            save_input (bool): Whether to save the input arguments and keyword arguments in the cache file. default: True
        """
        self._cache_dir = cache_dir
        self._save_input = save_input
        os.makedirs(cache_dir, exist_ok=True)

    def get_cache_path(self, key: str) -> str:
        return os.path.join(self._cache_dir, f"{key}.json")

    def get(self, key: str) -> Optional[Any]:
        path = self.get_cache_path(key)
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                return data['result']
        return None

    def set(self, key: str, value: Any, args: tuple | None = None, kwargs: dict | None = None) -> None:
        path = self.get_cache_path(key)
        cache_entry = CacheEntry(
            result=value,
            args=args if self._save_input else "save_input=False",
            kwargs=kwargs if self._save_input else "save_input=False"
        )
        with open(path, 'w') as f:
            json.dump(cache_entry.to_dict(), f, indent=4)

    def clear(self) -> None:
        """Clear all cache files"""
        for f in os.listdir(self._cache_dir):
            if f.endswith('.json'):
                os.remove(os.path.join(self._cache_dir, f))


def cached[F: Callable[..., Any]](provider: CacheInterface = CacheManager(), prefix: str = "") -> Callable[[F], F]:
    """
    Decorator that caches function results in JSON files. The cache key is generated from the function name and argument values.

    Args:
        provider (CacheInterface): The cache manager to use. default: CacheManager()
        prefix (str): The prefix to use for the cache file names. default: ""

    Usage:
    @cached(provider=CacheManager(), prefix="myapp")
    def my_function(arg1, arg2):
        return expensive_computation(arg1, arg2)
        
    @cached() # Use the default cache manager
    def my_function(arg1, arg2):
        return expensive_computation(arg1, arg2)
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache manager from first arg (self) if it exists
            sha = sha256((str(args) + str(kwargs)).encode('utf-8')).hexdigest()
            key = f"{prefix}_{func.__name__}_{sha}"

            if result := provider.get(key):
                return result

            result = func(*args, **kwargs)
            provider.set(key, result, args=args, kwargs=kwargs)
            return result
        return cast(F, wrapper)
    return decorator
