from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import Config

config = Config()
DATABASE_URL = f"mysql+pymysql://{config.db_user}:{config.db_password}@{config.db_host}/{config.db_name}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()