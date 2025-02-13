import json
import os
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from hashlib import sha256
from typing import Any, Callable, Optional, Protocol, cast


class CacheInterface(Protocol):
    def get(self, func_name: str, args: tuple, kwargs: dict) -> Optional[Any]: ...
    def set(self, func_name: str, args: tuple, kwargs: dict, return_value: Any = None) -> None: ...


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

    def get_cache_path(self, func_name: str, args: tuple | None = None, kwargs: dict | None = None) -> str:
        sha = sha256((str(args) + str(kwargs)).encode('utf-8')).hexdigest()
        return os.path.join(self._cache_dir, func_name, f"{sha}.json")

    def get(self, func_name: str, args: tuple | None, kwargs: dict | None) -> Optional[Any]:
        path = self.get_cache_path(func_name, args, kwargs)
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                return data['result']
        return None

    def set(self, func_name: str, args: tuple | None = None, kwargs: dict | None = None, return_value: Any = None) -> None:
        path = self.get_cache_path(func_name, args, kwargs)
        cache_entry = CacheEntry(
            result=return_value,
            args=args if self._save_input else "save_input=False",
            kwargs=kwargs if self._save_input else "save_input=False"
        )
        
        folder = os.path.dirname(path)
        os.makedirs(folder, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(cache_entry.to_dict(), f, indent=4)

    def clear(self) -> None:
        """Clear all cache files"""
        os.rmdir(self._cache_dir)

def cached[F: Callable[..., Any]](provider: CacheInterface = CacheManager()) -> Callable[[F], F]:
    """
    Decorator that caches function results in JSON files. The cache key is generated from the function name and argument values.

    Args:
        provider (CacheInterface): The cache manager to use. default: CacheManager()

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
            if result := provider.get(func.__name__, args, kwargs):
                return result

            result = func(*args, **kwargs)
            provider.set(func.__name__, args, kwargs, result)
            return result
        return cast(F, wrapper)
    return decorator
