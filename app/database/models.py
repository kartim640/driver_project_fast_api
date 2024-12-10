from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    name = Column(String(255))
    profile_picture = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    storage_used = Column(Float, default=0.0)  # in MB
    storage_limit = Column(Float, default=1024.0)  # 1GB default limit

    # Relationship with files
    files = relationship("File", back_populates="owner")


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255))
    original_filename = Column(String(255))
    file_path = Column(String(255))
    file_size = Column(Float)  # in MB
    file_type = Column(String(50))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))

    # Relationship with user
    owner = relationship("User", back_populates="files")