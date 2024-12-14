from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import User
from starlette.responses import RedirectResponse
from authlib.integrations.base_client import OAuthError
from typing import Optional, Dict, Any
from app.config import Config
from app.utils.security import Security
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AuthController:
    def __init__(self):
        self.config = Config()
        self.templates = Jinja2Templates(directory="templates")
        self.oauth = self.config.oauth
        self.security = Security()
        self.admin_emails = self.config.security.admin_emails

    async def handle_index(self, request: Request):
        """Handle index page request"""
        try:
            await self.refresh_session(request)  # Add session refresh here
            user = request.session.get('user')
            if user:
                return RedirectResponse('/dashboard')
            return self.templates.TemplateResponse("home.html", {"request": request})
        except Exception as e:
            logger.error(f"Error handling index: {e}")
            return self.templates.TemplateResponse(
                "error.html",
                {"request": request, "error": "An error occurred"}
            )

    async def handle_login(self, request: Request):
        """Handle login request"""
        try:
            await self.refresh_session(request)  # Add session refresh here
            user = request.session.get('user')
            if user:
                return RedirectResponse('/dashboard')

            redirect_uri = request.url_for('auth')
            logger.debug(f"Login redirect URI: {redirect_uri}")
            return await self.oauth.google.authorize_redirect(request, redirect_uri)

        except Exception as e:
            logger.error(f"Login error: {e}")
            return self.templates.TemplateResponse(
                "error.html",
                {"request": request, "error": "Login failed"}
            )

    async def handle_auth(self, request: Request, db: Session):
        """Handle OAuth authentication callback"""
        try:
            token = await self.oauth.google.authorize_access_token(request)
            user_info = token.get('userinfo')

            if not user_info:
                raise HTTPException(status_code=400, detail="Failed to get user info")

            # Get or create user
            db_user = await self._get_or_create_user(db, user_info)

            # Create session
            user_data = self._create_session_data(user_info, db_user)
            request.session['user'] = user_data

            # Update last login
            await self._update_last_login(db, db_user)

            # Set session expiry (7 days)
            request.session['expires'] = self._get_session_expiry()

            logger.info(f"User authenticated successfully: {user_info['email']}")
            return RedirectResponse('/dashboard')

        except OAuthError as e:
            logger.error(f"OAuth error: {e}")
            return self.templates.TemplateResponse(
                'error.html',
                {'request': request, 'error': str(e)}
            )
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return self.templates.TemplateResponse(
                'error.html',
                {'request': request, 'error': "Authentication failed"}
            )

    async def handle_logout(self, request: Request):
        """Handle logout request"""
        try:
            # Clear all session data
            request.session.clear()
            return RedirectResponse('/')
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return RedirectResponse('/')

    async def _get_or_create_user(self, db: Session, user_info: dict) -> User:
        """Get existing user or create new one"""
        try:
            db_user = db.query(User).filter(User.email == user_info['email']).first()

            if not db_user:
                is_admin = user_info['email'] in self.admin_emails
                db_user = User(
                    email=user_info['email'],
                    name=user_info['name'],
                    profile_picture=user_info['picture'],
                    storage_limit=1024.0,  # 1GB default limit
                    is_admin=is_admin,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.add(db_user)
                db.commit()
                db.refresh(db_user)
                logger.info(f"New user created: {user_info['email']}, Admin: {is_admin}")
            else:
                # Update user information
                db_user.name = user_info['name']
                db_user.profile_picture = user_info['picture']

                # Update admin status if needed
                if db_user.email in self.admin_emails and not db_user.is_admin:
                    db_user.is_admin = True
                    logger.info(f"Updated admin status for user: {db_user.email}")

                db.commit()

            return db_user

        except Exception as e:
            logger.error(f"Error in get_or_create_user: {e}")
            db.rollback()
            raise

    def _create_session_data(self, user_info: dict, db_user: User) -> dict:
        """Create session data for user"""
        try:
            session_data = {
                'email': user_info['email'],
                'name': user_info['name'],
                'picture': user_info['picture'],
                'db_id': db_user.id,
                'is_admin': db_user.is_admin,
                'storage_limit': db_user.storage_limit,
                'created_at': datetime.utcnow().isoformat()
            }
            return session_data
        except Exception as e:
            logger.error(f"Error creating session data: {e}")
            raise

    async def _update_last_login(self, db: Session, user: User) -> None:
        """Update user's last login timestamp"""
        try:
            user.last_login = datetime.utcnow()
            db.commit()
            logger.debug(f"Updated last login for user: {user.email}")
        except Exception as e:
            logger.error(f"Error updating last login: {e}")
            db.rollback()
            raise

    def _get_session_expiry(self) -> str:
        """Get session expiry timestamp"""
        from datetime import timedelta
        return (datetime.utcnow() + timedelta(days=7)).isoformat()

    async def check_session(self, request: Request) -> bool:
        """Check if session is valid"""
        try:
            user = request.session.get('user')
            if not user:
                return False

            expires = request.session.get('expires')
            if not expires:
                return False

            expiry_time = datetime.fromisoformat(expires)
            return datetime.utcnow() < expiry_time

        except Exception as e:
            logger.error(f"Session check error: {e}")
            return False

    async def refresh_session(self, request: Request) -> None:
        """Refresh session expiry"""
        try:
            if await self.check_session(request):
                request.session['expires'] = self._get_session_expiry()
        except Exception as e:
            logger.error(f"Session refresh error: {e}")


# Create router and controller
router = APIRouter()
auth_controller = AuthController()


# Route definitions
@router.get("/")
async def index(request: Request):
    return await auth_controller.handle_index(request)


@router.get("/login")
async def login(request: Request):
    return await auth_controller.handle_login(request)


@router.get('/auth')
async def auth(request: Request, db: Session = Depends(get_db)):
    return await auth_controller.handle_auth(request, db)


@router.get('/logout')
async def logout(request: Request):
    return await auth_controller.handle_logout(request)


@router.get("/check-session")
async def check_session(request: Request):
    is_valid = await auth_controller.check_session(request)
    return {"valid": is_valid}


@router.post("/refresh-session")
async def refresh_session(request: Request):
    await auth_controller.refresh_session(request)
    return {"message": "Session refreshed"}


# Test routes
@router.get("/test-page")
async def test_page(request: Request):
    return auth_controller.templates.TemplateResponse(
        "test.html",
        {"request": request}
    )