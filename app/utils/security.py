from fastapi import HTTPException
from fastapi.security import HTTPBearer
from starlette.requests import Request
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta
import secrets
import logging
from app.database.models import User
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class Security:
    def __init__(self):
        self.secret_key = secrets.token_urlsafe(32)
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.bearer = HTTPBearer()

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create a new JWT access token"""
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )
            to_encode.update({"exp": expire})
            return jwt.encode(
                to_encode,
                self.secret_key,
                algorithm=self.algorithm
            )
        except Exception as e:
            logger.error(f"Token creation error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Could not create access token"
            )

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )
        except jwt.JWTError as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials"
            )

    async def get_current_user(
        self,
        request: Request,
        db: Session
    ) -> Optional[User]:
        """Get current user from session or token"""
        try:
            # Try session first
            user_data = request.session.get('user')
            if user_data:
                return db.query(User).filter(
                    User.id == user_data['db_id']
                ).first()

            # Try token authentication
            auth = request.headers.get('Authorization')
            if auth and auth.startswith('Bearer '):
                token = auth.split(' ')[1]
                payload = self.verify_token(token)
                return db.query(User).filter(
                    User.email == payload['email']
                ).first()

            return None

        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password (for future use with password auth)"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash password (for future use with password auth)"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)

    def verify_csrf_token(self, request: Request) -> bool:
        """Verify CSRF token"""
        try:
            session_token = request.session.get('csrf_token')
            form_token = request.headers.get('X-CSRF-Token')
            return session_token and form_token and session_token == form_token
        except Exception as e:
            logger.error(f"CSRF verification error: {e}")
            return False

    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)

# Create global instance
security = Security()