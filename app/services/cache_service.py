import json

from app.database.redis_client import redis_client


class CacheService:
    FILE_META_TTL_SECONDS = 300

    @staticmethod
    def file_meta_key(file_id):
        return f"wp:files:{file_id}:meta"

    @staticmethod
    def profile_key(user_id):
        return f"wp:users:{user_id}:profile"

    @staticmethod
    def get_json(key):
        value = redis_client.get(key)
        if not value:
            return None

        return json.loads(value)

    @staticmethod
    def set_json(key, value, ttl_seconds):
        redis_client.setex(key, ttl_seconds, json.dumps(value))

    @staticmethod
    def delete(key):
        redis_client.delete(key)
