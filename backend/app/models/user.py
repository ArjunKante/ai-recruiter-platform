from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import Column, DateTime, Enum, Integer, String

from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    RECRUITER = "recruiter"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.RECRUITER, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
