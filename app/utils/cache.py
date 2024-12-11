from functools import wraps
from typing import Callable, Any, Optional
import redis
import json
import pickle
from datetime import timedelta

class Cache:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis = redis.Redis(host=host, port=port, db=db)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = self.redis.get(key)
        if value:
            return pickle.loads(value)
        return None

    def set(self, key: str, value: Any, expire: int = 300):
        """Set value in cache"""
        self.redis.setex(key, expire, pickle.dumps(value))

    def delete(self, key: str):
        """Delete value from cache"""
        self.redis.delete(key)

def cache_response(expire: int = 300):
    """Decorator to cache endpoint responses"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return cached_response

            # Get fresh response
            response = await func(*args, **kwargs)

            # Cache the response
            cache.set(cache_key, response, expire)

            return response
        return wrapper
    return decorator

# Initialize cache
cache = Cache()