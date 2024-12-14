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
import yaml
import json


@dataclass
class DatabaseConfig:
    host: str
    user: str
    password: str
    name: str
    port: int = 3306
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800

    @property
    def database_url(self) -> str:
        # Fix the URL format
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}/{self.name}"


@dataclass
class OAuthConfig:
    client_id: str
    client_secret: str
    redirect_url: str
    scopes: List[str] = None

    def __post_init__(self):
        if self.scopes is None:
            self.scopes = ['email', 'openid', 'profile']


@dataclass
class ServerConfig:
    host: str
    port: int
    debug: bool
    workers: int = 4
    reload: bool = False
    cors_origins: List[str] = None

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]


@dataclass
class StorageConfig:
    base_path: str
    max_file_size: int  # in MB
    allowed_extensions: Dict[str, List[str]]
    preview_size: tuple = (200, 200)
    temp_dir: str = "/tmp"
    cleanup_interval: int = 3600  # in seconds


@dataclass
class SecurityConfig:
    secret_key: str
    token_expire_minutes: int = 30
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration: int = 300  # in seconds
    admin_emails: List[str] = None

    def __post_init__(self):
        if self.admin_emails is None:
            self.admin_emails = ['kartim640@gmail.com', 'karthikm640@gmail.com']


@dataclass
class LoggingConfig:
    level: str
    file_path: str
    max_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


@dataclass
class CacheConfig:
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_db: int = 0
    default_timeout: int = 300
    key_prefix: str = 'myapp:'


@dataclass
class WebsiteConfig:
    title: str
    description: str
    version: str
    contact_email: str
    support_phone: str = None
    maintenance_mode: bool = False


class Config:
    """Application configuration class"""

    def __init__(self):
        self._init_paths()
        self._load_env()
        self._init_parser()
        self._setup_configs()
        self._setup_logging()
        self.oauth = self._init_oauth()

    def _init_paths(self) -> None:
        """Initialize important paths"""
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = Path(os.path.expanduser("~")) / "data_requirements/lite_driver_dot_in"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Configuration files
        self.config_file = self.config_dir / "config.ini"
        self.env_file = self.config_dir / ".env"
        self.secrets_file = self.config_dir / "secrets.yaml"

    def _load_env(self) -> None:
        """Load environment variables"""
        if self.env_file.exists():
            load_dotenv(self.env_file)
        self.environment = os.getenv("ENVIRONMENT", "development")

    def _init_parser(self) -> None:
        """Initialize configuration parser"""
        self.parser = ConfigParser()
        if self.config_file.exists():
            self.parser.read(self.config_file)

        # Load secrets if available
        self.secrets = {}
        if self.secrets_file.exists():
            with open(self.secrets_file) as f:
                self.secrets = yaml.safe_load(f)

    def _setup_configs(self) -> None:
        """Setup all configuration objects"""
        self.db = self._setup_database_config()
        self.oauth_config = self._setup_oauth_config()
        self.server = self._setup_server_config()
        self.storage = self._setup_storage_config()
        self.security = self._setup_security_config()
        self.logging = self._setup_logging_config()
        self.cache = self._setup_cache_config()
        self.website = self._setup_website_config()

        # Additional configurations
        self.sentry_dsn = os.getenv("SENTRY_DSN")
        self.cors_origins = self.server.cors_origins
        self.secret_key = self.security.secret_key

    def _setup_database_config(self) -> DatabaseConfig:
        """Setup database configuration"""
        return DatabaseConfig(
            host=os.getenv("DB_HOST") or self.parser.get('database', 'host', fallback='localhost'),
            user=os.getenv("DB_USER") or self.parser.get('database', 'user', fallback='root'),
            password=os.getenv("DB_PASSWORD") or self.parser.get('database', 'password', fallback=''),
            name=os.getenv("DB_NAME") or self.parser.get('database', 'name', fallback='driver_project'),
            port=int(os.getenv("DB_PORT") or self.parser.get('database', 'port', fallback='3306')),
            echo=self.parser.getboolean('database', 'echo', fallback=False)
        )

    def _setup_oauth_config(self) -> OAuthConfig:
        """Setup OAuth configuration"""
        return OAuthConfig(
            client_id=os.getenv("client-id")or self.parser.get('google', 'client-id', fallback=''),
            client_secret=os.getenv("client-secret") or self.parser.get('google', 'client-secret', fallback=''),
            redirect_url=self.parser.get('settings', 'redirect_url', fallback='https://www.litedriver.in/auth')
        )

    def _setup_server_config(self) -> ServerConfig:
        """Setup server configuration"""
        return ServerConfig(
            host=self.parser.get('server', 'host', fallback='0.0.0.0'),
            port=self.parser.getint('server', 'port', fallback=5000),
            debug=self.environment == 'development',
            workers=self.parser.getint('server', 'workers', fallback=4),
            reload=self.environment == 'development'
        )

    def _setup_storage_config(self) -> StorageConfig:
        """Setup storage configuration"""
        allowed_extensions = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
            'document': ['.pdf', '.doc', '.docx', '.txt'],
            'video': ['.mp4', '.avi', '.mov'],
            'audio': ['.mp3', '.wav', '.ogg']
        }

        return StorageConfig(
            base_path=self.parser.get('storage', 'base_path', fallback='storage'),
            max_file_size=self.parser.getint('storage', 'max_file_size', fallback=100),
            allowed_extensions=allowed_extensions
        )

    def _setup_security_config(self) -> SecurityConfig:
        """Setup security configuration"""
        return SecurityConfig(
            secret_key=os.getenv("SECRET_KEY") or base64.urlsafe_b64encode(os.urandom(32)).decode(),
            admin_emails=self.parser.get(
                'security',
                'admin_emails',
                fallback='kartim640@gmail.com,karthikm640@gmail.com'
            ).split(',')
        )

    def _setup_logging_config(self) -> LoggingConfig:
        """Setup logging configuration"""
        return LoggingConfig(
            level=self.parser.get('logging', 'level', fallback='INFO'),
            file_path=self.parser.get('logging', 'file_path', fallback='logs/app.log')
        )

    def _setup_cache_config(self) -> CacheConfig:
        """Setup cache configuration"""
        return CacheConfig(
            redis_host=self.parser.get('cache', 'redis_host', fallback='localhost'),
            redis_port=self.parser.getint('cache', 'redis_port', fallback=6379)
        )

    def _setup_website_config(self) -> WebsiteConfig:
        """Setup website configuration"""
        return WebsiteConfig(
            title=self.parser.get('website', 'title', fallback='File Storage System'),
            description=self.parser.get('website', 'description', fallback='A secure file storage system'),
            version=self.parser.get('website', 'version', fallback='1.0.0'),
            contact_email=self.parser.get('website', 'contact_email', fallback='support@example.com')
        )

    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        log_dir = Path(self.logging.file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=getattr(logging, self.logging.level.upper()),
            format=self.logging.format,
            handlers=[
                RotatingFileHandler(
                    self.logging.file_path,
                    maxBytes=self.logging.max_size,
                    backupCount=self.logging.backup_count
                ),
                logging.StreamHandler()
            ]
        )

    def _init_oauth(self) -> OAuth:
        """Initialize OAuth"""
        oauth = OAuth()
        oauth.register(
            name='google',
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_id=self.oauth_config.client_id,
            client_secret=self.oauth_config.client_secret,
            client_kwargs={
                'scope': ' '.join(self.oauth_config.scopes),
                'redirect_url': self.oauth_config.redirect_url
            }
        )
        return oauth

    def save_config(self) -> None:
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                self.parser.write(f)
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")

    def reload_config(self) -> None:
        """Reload configuration from files"""
        self._load_env()
        self._init_parser()
        self._setup_configs()

    def get_environment_config(self) -> dict:
        """Get environment-specific configuration"""
        env_config = {
            'development': {
                'debug': True,
                'reload': True,
                'log_level': 'DEBUG'
            },
            'production': {
                'debug': False,
                'reload': False,
                'log_level': 'INFO'
            },
            'testing': {
                'debug': True,
                'reload': False,
                'log_level': 'DEBUG'
            }
        }
        return env_config.get(self.environment, env_config['development'])


# Create global instance
config = Config()