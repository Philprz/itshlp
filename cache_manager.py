# cache_manager.py
import hashlib
import json
import redis
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from db.models import CachedQuery, CachedFormat

class CacheManager:
    def __init__(self, db_url, redis_url="redis://localhost:6379/0"):
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def compute_key(self, query, filters, limit):
        base = {
            "query": query.strip().lower(),
            "filters": filters,
            "limit": limit
        }
        raw = json.dumps(base, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get_raw_results(self, cache_key):
        val = self.redis.get(f"RAW:{cache_key}")
        if val:
            return json.loads(val)

        # fallback DB
        session = self.Session()
        result = session.query(CachedQuery).filter_by(id=cache_key).first()
        if result:
            self.redis.setex(f"RAW:{cache_key}", 3600, json.dumps(result.raw_results))
            return result.raw_results
        return None

    def store_raw_results(self, cache_key, query, filters, limit, embedding, raw_results):
        self.redis.setex(f"RAW:{cache_key}", 3600, json.dumps(raw_results))

        session = self.Session()
        entry = CachedQuery(
            id=cache_key,
            query=query,
            filters=filters,
            limit=limit,
            embedding=int(embedding),
            raw_results=raw_results
        )
        session.merge(entry)
        session.commit()

    def get_format(self, format_key):
        val = self.redis.get(f"FMT:{format_key}")
        if val:
            return json.loads(val)

        session = self.Session()
        result = session.query(CachedFormat).filter_by(id=format_key).first()
        if result:
            self.redis.setex(f"FMT:{format_key}", 3600, json.dumps({
                "content": result.content,
                "sources": result.sources,
                "meta": result.meta
            }))
            return {
                "content": result.content,
                "sources": result.sources,
                "meta": result.meta
            }
        return None

    def store_format(self, format_key, format_type, content, sources, meta):
        self.redis.setex(f"FMT:{format_key}", 3600, json.dumps({
            "content": content,
            "sources": sources,
            "meta": meta
        }))

        session = self.Session()
        entry = CachedFormat(
            id=format_key,
            format_type=format_type,
            content=content,
            sources=sources,
            meta=meta
        )
        session.merge(entry)
        session.commit()
