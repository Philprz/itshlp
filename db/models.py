# db/models.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON
from datetime import datetime

Base = declarative_base()

class CachedQuery(Base):
    __tablename__ = "cached_queries"

    id = Column(String, primary_key=True)  # hash unique
    query = Column(Text)
    filters = Column(JSON)
    limit = Column(Integer)
    embedding = Column(Integer)  # 1 ou 0
    raw_results = Column(JSON)  # liste de payloads
    created_at = Column(DateTime, default=datetime.utcnow)

class CachedFormat(Base):
    __tablename__ = "cached_formats"

    id = Column(String, primary_key=True)  # format_type + hash
    format_type = Column(String)  # "Summary", "Guide"
    content = Column(Text)
    sources = Column(String)
    meta = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
