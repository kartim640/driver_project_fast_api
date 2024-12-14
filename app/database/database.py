from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from app.config import Config
from app.database.models import Base
from contextlib import contextmanager
from typing import Generator
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, config: Config):
        self.config = config
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def _create_engine(self):
        """Create database engine with connection pooling"""
        return create_engine(
            self.config.db.database_url,
            poolclass=QueuePool,
            pool_size=self.config.db.pool_size,
            max_overflow=self.config.db.max_overflow,
            pool_timeout=self.config.db.pool_timeout,
            pool_recycle=self.config.db.pool_recycle,
            echo=self.config.db.echo
        )

    def init_db(self):
        """Initialize database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def get_db(self) -> Generator[Session, None, None]:
        """Get database session"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def get_db_context(self) -> Generator[Session, None, None]:
        """Context manager for database sessions"""
        db = self.SessionLocal()
        try:
            yield db
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            db.close()

# Create database instance
config = Config()
db = Database(config)

# Initialize database
db.init_db()

# Export dependencies
get_db = db.get_db
get_db_context = db.get_db_context
engine = db.engine  # Export the engine