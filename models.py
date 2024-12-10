from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    email = Column(String, unique=True)
    fullname = Column(String)
    is_active = Column(Boolean, default=True)
    two_factor_enabled = Column(Boolean, default=False)
    oauth_accounts = relationship("OAuthAccount", back_populates="user")


class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    original_filename = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'))

    user = relationship("User", back_populates="files")


class OAuthAccount(Base):
    __tablename__ = 'oauth_accounts'

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))

    user = relationship("User", back_populates="oauth_accounts")
