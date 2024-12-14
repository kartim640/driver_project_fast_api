from functools import wraps
from fastapi import HTTPException
from starlette.requests import Request
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class AuthDecorator:
    @staticmethod
    def require_auth(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user = request.session.get('user')
            if not user:
                raise HTTPException(status_code=401, detail="Not authenticated")
            return await func(request, *args, **kwargs)

        return wrapper

    @staticmethod
    def require_admin(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user = request.session.get('user')
            if not user:
                raise HTTPException(status_code=401, detail="Not authenticated")

            admin_emails = ['kartim640@gmail.com', 'karthikm640@gmail.com']
            if user['email'] not in admin_emails:
                raise HTTPException(status_code=403, detail="Admin access required")

            return await func(request, *args, **kwargs)

        return wrapper


# Create instances
auth_decorator = AuthDecorator()
require_auth = auth_decorator.require_auth
require_admin = auth_decorator.require_admin