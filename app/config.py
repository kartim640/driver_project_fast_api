import os
from pathlib import Path
from configparser import ConfigParser
from dotenv import load_dotenv
from typing import Dict, Any, List
import base64
from authlib.integrations.starlette_client import OAuth
import logging
from logging.handlers import RotatingFileHandler


class Config:
    """Application configuration class"""

    def __init__(self):
        # Base paths
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = Path(os.path.expanduser("~")) / "data_requirements/lite_driver_dot_in"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Config files
        self.config_file = self.config_dir / "config.ini"
        self.env_file = self.config_dir / ".env"

        # Load configurations
        self._load_env()
        self._load_config()
        self._setup_logging()

        # Initialize OAuth
        self.oauth = self._init_oauth()

    def _load_env(self) -> None:
        """Load environment variables from .env file"""
        if self.env_file.exists():
            load_dotenv(self.env_file)

    def _load_config(self) -> None:
        """Load configuration from INI file"""
        self.parser = ConfigParser()

        if self.config_file.exists():
            self.parser.read(self.config_file)

        # Database settings
        self.db_config = {
            'host': os.getenv("DB_HOST") or self.parser.get('database', 'host', fallback='localhost'),
            'user': os.getenv("DB_USER") or self.parser.get('database', 'user', fallback='root'),
            'password': os.getenv("DB_PASSWORD") or self.parser.get('database', 'password', fallback=''),
            'name': os.getenv("DB_NAME") or self.parser.get('database', 'name', fallback='driver_project'),
            'echo': self.parser.getboolean('database', 'echo', fallback=False)
        }

        # OAuth settings
        self.client_id = os.getenv("client-id") or self.parser.get('google', 'client-id')
        self.client_secret = os.getenv("client-secret") or self.parser.get('google', 'client-secret')
        self.redirect_url = self.parser.get('settings', 'redirect_url')

        # Server settings
        self.server_config = {
            'host': self.parser.get('settings', 'ip_address', fallback='0.0.0.0'),
            'port': self.parser.getint('settings', 'port', fallback=5000),
            'debug': self.parser.getboolean('settings', 'debug', fallback=False)
        }

        # Upload settings
        self.upload_config = {
            'max_file_size': self.parser.getint('upload', 'max_file_size', fallback=100),
            'allowed_extensions': self.parser.get(
                'upload',
                'allowed_extensions',
                fallback='.txt,.pdf,.png,.jpg,.jpeg,.gif,.doc,.docx,.xls,.xlsx'
            ).split(',')
        }

        self.storage_config = {
            'base_path': '/media/karti/lite_driver',
            'allowed_extensions': {
                'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
                'document': ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx'],
                'video': ['.mp4', '.avi', '.mov', '.wmv'],
                'audio': ['.mp3', '.wav', '.ogg']
            },
            'preview_size': (200, 200),  # thumbnail size
            'max_file_size': 100 * 1024 * 1024  # 100MB
        }

        # Create base storage directory
        os.makedirs(self.storage_config['base_path'], exist_ok=True)

        # Generate secret key
        self.secret_key = self._generate_secret_key()

    def _setup_logging(self) -> None:
        """Configure application logging"""
        log_dir = self.base_dir / "logs"
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                RotatingFileHandler(
                    log_dir / "app.log",
                    maxBytes=10485760,  # 10MB
                    backupCount=5
                ),
                logging.StreamHandler()
            ]
        )

    def _generate_secret_key(self) -> str:
        """Generate a secure secret key for sessions"""
        return base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')

    def _init_oauth(self) -> OAuth:
        """Initialize OAuth with Google configuration"""
        oauth = OAuth()
        oauth.register(
            name='google',
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_id=self.client_id,
            client_secret=self.client_secret,
            client_kwargs={
                'scope': 'email openid profile',
                'redirect_url': self.redirect_url
            }
        )
        return oauth

    @property
    def database_url(self) -> str:
        """Get the database URL"""
        return f"mysql+pymysql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}/{self.db_config['name']}"
