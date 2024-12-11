from functools import wraps
from fastapi import HTTPException
from starlette.requests import Request
from typing import Callable
import logging

logger = logging.getLogger(__name__)

def require_auth(func: Callable):
    """Decorator to check if user is authenticated"""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user = request.session.get('user')
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return await func(request, *args, **kwargs)
    return wrapper

def handle_exceptions(func: Callable):
    """Decorator to handle exceptions uniformly"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    return wrapper