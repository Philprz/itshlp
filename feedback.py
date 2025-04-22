# feedback.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    query = Column(Text)
    format = Column(String)
    rating = Column(Integer)
    comment = Column(Text)
    submitted_at = Column(DateTime, default=datetime.utcnow)
