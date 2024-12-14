from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class BaseModel:
    """Base class for all models"""
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert model to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class User(Base, BaseModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    name = Column(String(255))
    profile_picture = Column(String(255))
    storage_used = Column(Float, default=0.0)  # in MB
    storage_limit = Column(Float, default=1024.0)  # 1GB default limit
    is_admin = Column(Boolean, default=False)  # Add this line
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)

    # Relationships
    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")

    @property
    def storage_percentage(self):
        """Calculate storage usage percentage"""
        return (self.storage_used / self.storage_limit) * 100 if self.storage_limit > 0 else 0

    def update_storage_used(self, size_change: float):
        """Update storage used"""
        self.storage_used = max(0, self.storage_used + size_change)

class File(Base, BaseModel):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    preview_path = Column(String(255))
    file_type = Column(String(50))
    file_size = Column(Float)  # in MB
    user_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    owner = relationship("User", back_populates="files")

    @property
    def file_extension(self):
        """Get file extension"""
        return self.original_filename.split('.')[-1] if '.' in self.original_filename else ''

    @property
    def formatted_size(self):
        """Format file size for display"""
        if self.file_size < 1:
            return f"{self.file_size * 1024:.2f} KB"
        return f"{self.file_size:.2f} MB"