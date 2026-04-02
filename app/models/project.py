from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from datetime import datetime
from app.database import Base
from sqlalchemy.orm import relationship

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="In Progress")
    deadline = Column(DateTime, nullable=True) # Новое поле для даты
    created_at = Column(DateTime, default=datetime.utcnow)
    # ВОТ ЭТОЙ СТРОКИ НЕ ХВАТАЕТ:
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # И обратная связь, чтобы проект "знал" своего владельца
    owner = relationship("User", back_populates="projects")