from fastapi import HTTPException
import time
from collections import defaultdict
from typing import Dict, Tuple
import threading


class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = threading.Lock()

    def _cleanup_old_requests(self, ip: str):
        """Remove requests older than 1 minute"""
        current_time = time.time()
        with self.lock:
            self.requests[ip] = [
                req_time for req_time in self.requests[ip]
                if current_time - req_time < 60
            ]

    def check_rate_limit(self, ip: str) -> Tuple[bool, float]:
        """Check if request is within rate limit"""
        self._cleanup_old_requests(ip)

        with self.lock:
            requests = self.requests[ip]
            if len(requests) >= self.requests_per_minute:
                oldest_request = requests[0]
                time_until_reset = 60 - (time.time() - oldest_request)
                return False, max(0, time_until_reset)

            self.requests[ip].append(time.time())
            return True, 0


def rate_limit(limiter: RateLimiter):
    """Decorator for rate limiting endpoints"""

    def decorator(func):
        async def wrapper(request, *args, **kwargs):
            client_ip = request.client.host
            allowed, wait_time = limiter.check_rate_limit(client_ip)

            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Please try again in {wait_time:.1f} seconds"
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator