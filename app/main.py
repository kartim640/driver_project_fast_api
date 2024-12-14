import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.config import Config
from app.routes import auth, file, admin
from app.database.database import db
from app.database.models import Base
import os
from fastapi.responses import JSONResponse, RedirectResponse
from prometheus_client import make_asgi_app
from app.utils.metrics import track_metrics
from app.utils.rate_limiter import RateLimiter
import sentry_sdk
from typing import Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class Application:
    def __init__(self):
        self.config = Config()
        self.templates = Jinja2Templates(directory="templates")
        self.rate_limiter = RateLimiter()
        self._init_sentry()
        self.app = self._create_app()

    def _init_sentry(self):
        """Initialize Sentry for error tracking"""
        if hasattr(self.config, 'sentry_dsn') and self.config.sentry_dsn:
            sentry_sdk.init(
                dsn=self.config.sentry_dsn,
                traces_sample_rate=1.0,
                environment=self.config.environment
            )

    def _create_app(self) -> FastAPI:
        """Create and configure FastAPI application"""
        app = FastAPI(
            title=self.config.website.title,
            description=self.config.website.description,
            version=self.config.website.version
        )

        self._configure_middleware(app)
        self._configure_routes(app)
        self._configure_exception_handlers(app)
        self._configure_static_files(app)
        self._init_database()

        return app

    async def session_middleware(self, request: Request, call_next: Callable):
        """Custom middleware for session handling"""
        try:
            # Check and refresh session if needed
            if hasattr(request, 'session'):
                user = request.session.get('user')
                if user:
                    expires = request.session.get('expires')
                    if expires:
                        expiry_time = datetime.fromisoformat(expires)
                        if datetime.utcnow() < expiry_time:
                            # Refresh session expiry
                            request.session['expires'] = (
                                    datetime.utcnow().replace(hour=23, minute=59, second=59) +
                                    timedelta(days=7)
                            ).isoformat()
                        else:
                            # Session expired, clear it
                            request.session.clear()
                            return RedirectResponse('/login')

            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Session middleware error: {e}")
            return await call_next(request)

    async def rate_limit_middleware(self, request: Request, call_next: Callable):
        """Custom middleware for rate limiting"""
        client_ip = request.client.host
        allowed, wait_time = self.rate_limiter.check_rate_limit(client_ip)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded. Please wait {wait_time:.1f} seconds"
                }
            )

        return await call_next(request)

    def _configure_middleware(self, app: FastAPI):
        """Configure middleware"""
        # Add custom middleware
        app.middleware("http")(self.session_middleware)
        app.middleware("http")(self.rate_limit_middleware)

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add session middleware
        app.add_middleware(
            SessionMiddleware,
            secret_key=self.config.secret_key,
            session_cookie="session",
            max_age=7 * 24 * 60 * 60,  # 7 days
            same_site="lax",
            https_only=self.config.environment == "production"
        )

    def _configure_routes(self, app: FastAPI):
        """Configure routes and routers"""

        # Add route for health check
        @app.get("/health")
        async def health_check():
            return {"status": "healthy"}

        # Include routers
        app.include_router(auth.router)
        app.include_router(file.router)
        app.include_router(admin.router)

        # Mount metrics
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)

    def _configure_exception_handlers(self, app: FastAPI):
        """Configure global exception handlers"""

        @app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            logger.error(f"Global exception: {exc}", exc_info=True)

            # Handle different types of exceptions
            if isinstance(exc, HTTPException):
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"detail": exc.detail}
                )

            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )

    def _configure_static_files(self, app: FastAPI):
        """Configure static files"""
        try:
            static_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "static"
            )

            # Ensure static directory exists
            os.makedirs(static_dir, exist_ok=True)

            # Mount static files
            app.mount("/static", StaticFiles(directory=static_dir), name="static")

            logger.info(f"Static files configured: {static_dir}")
        except Exception as e:
            logger.error(f"Error configuring static files: {e}")
            raise

    def _init_database(self):
        """Initialize database"""
        try:
            Base.metadata.create_all(bind=db.engine)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise

    @property
    def instance(self) -> FastAPI:
        """Get FastAPI application instance"""
        return self.app

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the application (for development)"""
        import uvicorn
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            reload=self.config.environment == "development"
        )


# Create application instance
app_instance = Application()
app = app_instance.instance

# Make sure templates directory exists
os.makedirs("templates", exist_ok=True)

# This is important - it makes the app instance available for import
__all__ = ['app']


# Add startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")
    # Add any startup tasks here


# Add shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")
    # Add any cleanup tasks here