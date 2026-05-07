import hashlib
from typing import Dict, Any, Optional
from .bloom_filter import BloomFilter
from core.redis_client import RedisClient


class DedupManager:
    _instance = None
    _bloom_filters = {}

    def __new__(cls, config=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config=None):
        if config and not hasattr(self, '_initialized'):
            self._config = config
            self._redis_client = RedisClient(config)
            self._dedup_config = config.get('dedup', {})
            self._initialized = True

    def get_bloom_filter(self, source_name: str) -> BloomFilter:
        if source_name not in self._bloom_filters:
            capacity = self._dedup_config.get('bloom_filter_capacity', 1000000)
            error_rate = self._dedup_config.get('bloom_filter_error_rate', 0.001)
            self._bloom_filters[source_name] = BloomFilter(
                name=source_name,
                capacity=capacity,
                error_rate=error_rate
            )
        return self._bloom_filters[source_name]

    def generate_fingerprint(self, content: str, method: str = 'url') -> str:
        if method == 'url':
            return hashlib.md5(content.encode('utf-8')).hexdigest()
        elif method == 'content':
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        else:
            return hashlib.md5(content.encode('utf-8')).hexdigest()

    def check_duplicate(self, source_name: str, content: str, method: str = 'url') -> bool:
        fingerprint = self.generate_fingerprint(content, method)

        if self._redis_client.is_connected():
            key = f"{self._dedup_config.get('key_prefix', 'infopulse:')}{source_name}:{fingerprint}"
            exists = self._redis_client.get_cache(key)
            if exists:
                return True
            self._redis_client.set_cache(key, '1', expire=86400 * 7)
            return False
        else:
            bloom_filter = self.get_bloom_filter(source_name)
            if fingerprint in bloom_filter:
                return True
            bloom_filter.add(fingerprint)
            return False

    def add_to_dedup(self, source_name: str, content: str, method: str = 'url'):
        fingerprint = self.generate_fingerprint(content, method)

        if self._redis_client.is_connected():
            key = f"{self._dedup_config.get('key_prefix', 'infopulse:')}{source_name}:{fingerprint}"
            self._redis_client.set_cache(key, '1', expire=86400 * 7)
        else:
            bloom_filter = self.get_bloom_filter(source_name)
            bloom_filter.add(fingerprint)

    def check_url_duplicate(self, source_name: str, url: str) -> bool:
        return self.check_duplicate(source_name, url, 'url')

    def check_content_duplicate(self, source_name: str, content: str) -> bool:
        return self.check_duplicate(source_name, content, 'content')

    def clear_source(self, source_name: str):
        if source_name in self._bloom_filters:
            del self._bloom_filters[source_name]

    def clear_all(self):
        self._bloom_filters.clear()