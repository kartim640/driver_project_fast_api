from fastapi import HTTPException
from fastapi.security import HTTPBearer
from starlette.requests import Request
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta
import secrets

security = HTTPBearer()

class Security:
    SECRET_KEY = secrets.token_urlsafe(32)
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    @classmethod
    def create_access_token(cls, data: Dict[str, Any]) -> str:
        """Create a new access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)

    @classmethod
    def verify_token(cls, token: str) -> Dict[str, Any]:
        """Verify and decode a token"""
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            return payload
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials"
            )

    @classmethod
    async def get_current_user(cls, request: Request) -> Optional[Dict[str, Any]]:
        """Get current user from session or token"""
        # First try session
        user = request.session.get('user')
        if user:
            return user

        # Then try token
        auth = request.headers.get('Authorization')
        if auth and auth.startswith('Bearer '):
            token = auth.split(' ')[1]
            return cls.verify_token(token)

        return None