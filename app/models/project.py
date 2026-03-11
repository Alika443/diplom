from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="In Progress")
    deadline = Column(DateTime, nullable=True) # Новое поле для даты
    created_at = Column(DateTime, default=datetime.utcnow)