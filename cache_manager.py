# cache_manager.py
import hashlib
import json
import redis
import os
import socket
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Text, JSON, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

def is_development_env():
    """Détecte si on est en environnement local (dev)"""
    env = os.getenv("ENVIRONMENT", "").lower()
    if env in ["dev", "development"]:
        return True
    if env in ["prod", "production"]:
        return False

    # Déduction via hostname
    hostname = socket.gethostname().lower()
    if any(keyword in hostname for keyword in ["philippe", "local", "laptop", "pc"]):
        return True

    return False

class CachedResult(Base):
    __tablename__ = "cached_results"
    id = Column(Integer, primary_key=True)
    cache_key = Column(String, index=True)
    query = Column(Text)
    filters = Column(JSON)
    limit = Column(Integer)
    use_embedding = Column(String)
    content = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class CachedFormat(Base):
    __tablename__ = "cached_formats"
    id = Column(Integer, primary_key=True)
    format_key = Column(String, index=True)
    format_type = Column(String)
    content = Column(JSON)
    sources = Column(String)
    meta = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class CacheManager:
    def __init__(self, db_url=None, redis_url=None):
        self.is_dev = is_development_env()
        self.redis = None

        if redis_url and not self.is_dev:
            try:
                self.redis = redis.Redis.from_url(redis_url)
                self.redis.ping()
                print("[✅] Redis connecté.")
            except Exception as e:
                print(f"[⚠️] Redis inaccessible : {e}")
                self.redis = None
        else:
            print("[ℹ️] Redis désactivé en local.")

        self.db_enabled = bool(db_url)
        self.engine = create_engine(db_url) if db_url else None
        self.Session = sessionmaker(bind=self.engine) if self.engine else None

        if self.db_enabled:
            Base.metadata.create_all(self.engine)

    def compute_key(self, query, filters, limit):
        base_string = f"{query}-{json.dumps(filters, sort_keys=True)}-{limit}"
        return hashlib.sha256(base_string.encode()).hexdigest()

    def get_raw_results(self, cache_key):
        if self.redis:
            try:
                val = self.redis.get(f"RAW:{cache_key}")
                if val:
                    return json.loads(val)
            except Exception as e:
                print(f"[⚠️] Erreur Redis lecture : {e}")

        if self.db_enabled:
            session = self.Session()
            result = session.query(CachedResult).filter_by(cache_key=cache_key).first()
            if result:
                return result.content

        return None

    def store_raw_results(self, cache_key, query, filters, limit, use_embedding, content):
        if self.redis:
            try:
                self.redis.set(f"RAW:{cache_key}", json.dumps(content), ex=60 * 60 * 24)
            except Exception as e:
                print(f"[⚠️] Erreur Redis écriture : {e}")

        if self.db_enabled:
            session = self.Session()
            entry = CachedResult(
                cache_key=cache_key,
                query=query,
                filters=filters,
                limit=limit,
                use_embedding=str(use_embedding),
                content=content
            )
            session.add(entry)
            session.commit()

    def get_format(self, format_key):
        if self.redis:
            try:
                val = self.redis.get(f"FORMAT:{format_key}")
                if val:
                    return json.loads(val)
            except Exception as e:
                print(f"[⚠️] Erreur Redis lecture FORMAT : {e}")

        if self.db_enabled:
            session = self.Session()
            result = session.query(CachedFormat).filter_by(format_key=format_key).first()
            if result:
                return {
                    "content": result.content,
                    "sources": result.sources,
                    "meta": result.meta
                }

        return None

    def store_format(self, format_key, format_type, content, sources, meta=None):
        if self.redis:
            try:
                self.redis.set(f"FORMAT:{format_key}", json.dumps({
                    "content": content,
                    "sources": sources,
                    "meta": meta or {}
                }), ex=60 * 60 * 24)
            except Exception as e:
                print(f"[⚠️] Erreur Redis écriture FORMAT : {e}")

        if self.db_enabled:
            session = self.Session()
            entry = CachedFormat(
                format_key=format_key,
                format_type=format_type,
                content=content,
                sources=sources,
                meta=meta or {}
            )
            session.add(entry)
            session.commit()
