# app/models/task.py
from sqlalchemy import Column, Integer, String, ForeignKey, Date 
from sqlalchemy.orm import relationship
from app.database import Base

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    status = Column(String, default="To Do")
    deadline = Column(Date, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"))