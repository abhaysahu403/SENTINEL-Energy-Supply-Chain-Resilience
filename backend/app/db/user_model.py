from sqlalchemy import Column, String, DateTime, Boolean
import datetime as dt

from app.db.database import Base


class User(Base):
    """
    Real user accounts with hashed passwords and role-based access.
    Roles: procurement_manager | policy_desk | executive_viewer | admin
    """
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="executive_viewer")
    organization = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
