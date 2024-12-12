import os
from pathlib import Path
from configparser import ConfigParser
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
import base64
from authlib.integrations.starlette_client import OAuth
import logging
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    host: str
    user: str
    password: str
    name: str
    echo: bool

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}/{self.name}"


@dataclass
class OAuthConfig:
    client_id: str
    client_secret: str
    redirect_url: str


@dataclass
class ServerConfig:
    host: str
    port: int
    debug: bool


@dataclass
class UploadConfig:
    max_file_size: int
    allowed_extensions: List[str]


@dataclass
class StorageConfig:
    base_path: str
    allowed_extensions: Dict[str, List[str]]
    preview_size: tuple
    max_file_size: int

@dataclass
class WebsiteConfig:
    title: str
    description: str
    version: str

class Config:
    """Application configuration class"""

    def __init__(self):
        self._init_paths()
        self._load_env()
        self._init_parser()
        self._setup_configs()
        self._setup_logging()
        self.secret_key = self._generate_secret_key()
        self.oauth = self._init_oauth()

    def _init_paths(self) -> None:
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = Path(os.path.expanduser("~")) / "data_requirements/lite_driver_dot_in"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.ini"
        self.env_file = self.config_dir / ".env"

    def _load_env(self) -> None:
        if self.env_file.exists():
            load_dotenv(self.env_file)

    def _init_parser(self) -> None:
        self.parser = ConfigParser()
        if self.config_file.exists():
            self.parser.read(self.config_file)

    def _setup_configs(self) -> None:
        self.db = self._setup_database_config()
        self.oauth_config = self._setup_oauth_config()
        self.server = self._setup_server_config()
        self.upload = self._setup_upload_config()
        self.storage = self._setup_storage_config()

    def _setup_database_config(self) -> DatabaseConfig:
        return DatabaseConfig(
            host=os.getenv("DB_HOST") or self.parser.get('database', 'host', fallback='localhost'),
            user=os.getenv("DB_USER") or self.parser.get('database', 'user', fallback='root'),
            password=os.getenv("DB_PASSWORD") or self.parser.get('database', 'password', fallback=''),
            name=os.getenv("DB_NAME") or self.parser.get('database', 'name', fallback='driver_project'),
            echo=self.parser.getboolean('database', 'echo', fallback=False)
        )

    def _setup_oauth_config(self) -> OAuthConfig:
        return OAuthConfig(
            client_id=os.getenv("client-id") or self.parser.get('google', 'client-id'),
            client_secret=os.getenv("client-secret") or self.parser.get('google', 'client-secret'),
            redirect_url=self.parser.get('settings', 'redirect_url')
        )

    def _setup_server_config(self) -> ServerConfig:
        return ServerConfig(
            host=self.parser.get('settings', 'ip_address', fallback='0.0.0.0'),
            port=self.parser.getint('settings', 'port', fallback=5000),
            debug=self.parser.getboolean('settings', 'debug', fallback=False)
        )

    def _setup_upload_config(self) -> UploadConfig:
        return UploadConfig(
            max_file_size=self.parser.getint('upload', 'max_file_size', fallback=100),
            allowed_extensions=self.parser.get(
                'upload',
                'allowed_extensions',
                fallback='.txt,.pdf,.png,.jpg,.jpeg,.gif,.doc,.docx,.xls,.xlsx'
            ).split(',')
        )

    def _setup_website_config(self) -> WebsiteConfig:
        return WebsiteConfig(
            title=self.parser.get('website', 'title'),
            description=self.parser.get('website', 'description'),
            version=self.parser.get('website', 'version')
        )


    def _setup_storage_config(self) -> StorageConfig:
        storage_config = StorageConfig(
            base_path=self.parser.get('storage', 'base_path_1', fallback='driver_project'),
            allowed_extensions={
                'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
                'document': ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx'],
                'video': ['.mp4', '.avi', '.mov', '.wmv'],
                'audio': ['.mp3', '.wav', '.ogg']
            },
            preview_size=(200, 200),
            max_file_size=100 * 1024 * 1024
        )
        os.makedirs(storage_config.base_path, exist_ok=True)
        return storage_config

    def _setup_logging(self) -> None:
        log_dir = self.base_dir / "logs"
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                RotatingFileHandler(
                    log_dir / "app.log",
                    maxBytes=10485760,
                    backupCount=5
                ),
                logging.StreamHandler()
            ]
        )

    def _generate_secret_key(self) -> str:
        return base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')

    def _init_oauth(self) -> OAuth:
        oauth = OAuth()
        oauth.register(
            name='google',
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_id=self.oauth_config.client_id,
            client_secret=self.oauth_config.client_secret,
            client_kwargs={
                'scope': 'email openid profile',
                'redirect_url': self.oauth_config.redirect_url
            }
        )
        return oauth
