import os
import base64
from authlib.integrations.base_client import OAuthError
from fastapi import FastAPI, Depends
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from app.config import Config
from fastapi.staticfiles import StaticFiles
from app.routes import file
from app.database.models import User
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.routes import dashboard
from app.database.models import Base
from app.database.database import engine

Base.metadata.create_all(bind=engine)

class AppConfig:
    """
    This class handles the configuration for OAuth and FastAPI settings.
    """
    def __init__(self):
        self.config = Config()
        self.secret_key = self._generate_secret_key()
        self.oauth = self._init_oauth()

    @staticmethod
    def _generate_secret_key() -> str:
        """Generates a secure secret key for session middleware."""
        return base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')

    def _init_oauth(self) -> OAuth:
        """Initializes OAuth with Google client configuration."""
        oauth = OAuth()
        oauth.register(
            name='google',
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_id=self.config.client_id,
            client_secret=self.config.client_secret,
            client_kwargs={
                'scope': 'email openid profile',
                'redirect_url': self.config.redirect_url
            }
        )
        return oauth

class App:
    """
    This class contains the main FastAPI app logic.
    """
    def __init__(self):
        self.app = FastAPI()
        self.app.include_router(file.router)
        self.config = AppConfig()  # Initialize AppConfig
        self.app.add_middleware(
            SessionMiddleware,
            secret_key=self.config.secret_key,
        )
        self.templates = Jinja2Templates(directory="templates")
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
        # Include routers
        self.app.include_router(dashboard.router)
        self._init_routes()


    def _init_routes(self):
        """Define all routes for the FastAPI app."""

        @self.app.get("/")
        def index(request: Request):
            user = request.session.get('user')
            if user:
                return RedirectResponse('/welcome')  # Redirect logged-in users to the welcome page
            return self.templates.TemplateResponse("home.html", {"request": request})

        @self.app.get('/welcome')
        def welcome(request: Request):
            user = request.session.get('user')
            if not user:
                return RedirectResponse('/')  # Redirect to home if the user is not logged in
            return self.templates.TemplateResponse('welcome.html', {'request': request, 'user': user})

        @self.app.get("/login")
        async def login(request: Request):
            # Check if the user is already logged in
            user = request.session.get('user')
            if user:
                return RedirectResponse('/welcome')  # Redirect logged-in users to the welcome page
            url = request.url_for('auth')
            return await self.config.oauth.google.authorize_redirect(request, url)

        @self.app.get('/auth')
        async def auth(request: Request, db: Session = Depends(get_db)):
            # Check if the user is already logged in
            user = request.session.get('user')
            if user:
                return RedirectResponse('/dashboard')  # Changed from /welcome to /dashboard

            try:
                token = await self.config.oauth.google.authorize_access_token(request)
            except OAuthError as e:
                print(f"OAuth error: {e.error}")
                return self.templates.TemplateResponse('error.html', {'request': request, 'error': e.error})

            user = token.get('userinfo')
            if user:
                # Store user info in session
                request.session['user'] = dict(user)

                # Check if user exists in database, if not create new user
                db_user = db.query(User).filter(User.email == user['email']).first()
                if not db_user:
                    db_user = User(
                        email=user['email'],
                        name=user['name'],
                        profile_picture=user['picture'],
                        storage_limit=1024.0  # 1GB default limit
                    )
                    db.add(db_user)
                    db.commit()
                    db.refresh(db_user)

            return RedirectResponse('/dashboard')  # Changed from /welcome to /dashboard

        @self.app.get('/logout')
        def logout(request: Request):
            # user = request.session.get('user')
            # if not user:
            #     return RedirectResponse('/')
            request.session.pop('user', None)
            request.session.clear()
            return RedirectResponse('/')

        # Initialize and run the FastAPI app
def start_app():
    app_instance = App()
    return app_instance.app

app = start_app()
