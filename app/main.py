import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.config import Config
from app.routes import auth, file
from app.database.database import engine
from app.database.models import Base
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)


def create_app():
    app = FastAPI(
        title="Cloud Storage",
        description="A cloud storage application with Google OAuth",
        version="1.0.0"
    )

    config = Config()

    # Configure middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=config.secret_key,
    )

    # Get the absolute path to the static directory
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    logger.debug(f"Static directory path: {static_dir}")

    # Mount static files
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Include routers
    app.include_router(auth.router)
    app.include_router(file.router)

    # Store OAuth instance in app state
    app.state.oauth = config.oauth

    return app


app = create_app()

# This is important - it makes the app instance available for import
__all__ = ['app']