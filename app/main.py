import os
import base64
from authlib.integrations.base_client import OAuthError
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from app.config import Config
from fastapi.staticfiles import StaticFiles

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
        self.config = AppConfig()  # Initialize AppConfig
        self.app.add_middleware(
            SessionMiddleware,
            secret_key=self.config.secret_key,
        )
        self.templates = Jinja2Templates(directory="templates")
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
        self._init_routes()


    def _init_routes(self):
        """Define all routes for the FastAPI app."""
        @self.app.get("/")
        def index(request: Request):
            user = request.session.get('user')
            if user:
                return RedirectResponse('welcome')
            return self.templates.TemplateResponse("home.html", {"request": request})

        @self.app.get('/welcome')
        def welcome(request: Request):
            user = request.session.get('user')
            if not user:
                return RedirectResponse('/')
            return self.templates.TemplateResponse('welcome.html', {'request': request, 'user': user})

        @self.app.get("/login")
        async def login(request: Request):
            url = request.url_for('auth')
            return await self.config.oauth.google.authorize_redirect(request, url)

        @self.app.get('/auth')
        async def auth(request: Request):
            try:
                token = await self.config.oauth.google.authorize_access_token(request)
            except OAuthError as e:
                # Log error details for debugging
                print(f"OAuth error: {e.error}")
                return self.templates.TemplateResponse('error.html', {'request': request, 'error': e.error})
            user = token.get('userinfo')
            if user:
                request.session['user'] = dict(user)
            return RedirectResponse('welcome')

        @self.app.get('/logout')
        def logout(request: Request):
            # Safely pop 'user' from session if it exists
            request.session.pop('user', None)  # None is the default if 'user' doesn't exist
            request.session.clear()
            return RedirectResponse('/')


# Initialize and run the FastAPI app
def start_app():
    app_instance = App()
    return app_instance.app

app = start_app()  # Assign the FastAPI app to the `app` variable for uvicorn to run
