from sqlalchemy import Column, Integer, String, Enum
from app.database import Base
import enum
from sqlalchemy.orm import relationship

class UserRole(enum.Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    MANAGER = "manager"
    CUSTOMER = "customer"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default=UserRole.DEVELOPER.value)
    # Добавь эту строку обязательно!
    tasks = relationship("Task", back_populates="owner")
    
    # Если есть файл project.py, добавь и это:
    projects = relationship("Project", back_populates="owner")