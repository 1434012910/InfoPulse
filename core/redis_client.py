import redis
import hashlib
from typing import Optional, Dict, Any
from pybloom_live import ScalableBloomFilter


class RedisClient:
    _instance = None
    _client = None
    _bloom_filters = {}

    def __new__(cls, config=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config=None):
        if self._client is None and config:
            self._connect(config)

    def _connect(self, config: Dict[str, Any]):
        redis_config = config.get('redis', {})
        try:
            self._client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0),
                password=redis_config.get('password'),
                decode_responses=redis_config.get('decode_responses', True),
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            self._client.ping()
        except redis.ConnectionError as e:
            print(f"Redis连接失败: {e}")
            self._client = None

    def get_client(self) -> Optional[redis.Redis]:
        return self._client

    def is_connected(self) -> bool:
        if self._client is None:
            return False
        try:
            self._client.ping()
            return True
        except:
            return False

    def get_bloom_filter(self, name: str, capacity: int = 1000000, error_rate: float = 0.001) -> ScalableBloomFilter:
        if name not in self._bloom_filters:
            self._bloom_filters[name] = ScalableBloomFilter(
                initial_capacity=capacity,
                error_rate=error_rate
            )
        return self._bloom_filters[name]

    def check_duplicate(self, key: str, source_name: str, dedup_config: Dict) -> bool:
        bloom_filter = self.get_bloom_filter(
            f"{dedup_config.get('key_prefix', 'infopulse:')}{source_name}",
            dedup_config.get('bloom_filter_capacity', 1000000),
            dedup_config.get('bloom_filter_error_rate', 0.001)
        )
        return key in bloom_filter

    def add_to_bloom_filter(self, key: str, source_name: str, dedup_config: Dict):
        bloom_filter = self.get_bloom_filter(
            f"{dedup_config.get('key_prefix', 'infopulse:')}{source_name}",
            dedup_config.get('bloom_filter_capacity', 1000000),
            dedup_config.get('bloom_filter_error_rate', 0.001)
        )
        bloom_filter.add(key)

    def generate_fingerprint(self, content: str, method: str = 'url') -> str:
        if method == 'url':
            return hashlib.md5(content.encode('utf-8')).hexdigest()
        elif method == 'content':
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        else:
            return hashlib.md5(content.encode('utf-8')).hexdigest()

    def set_cache(self, key: str, value: str, expire: int = 3600):
        if self._client:
            try:
                self._client.setex(key, expire, value)
            except Exception as e:
                print(f"设置缓存失败: {e}")

    def get_cache(self, key: str) -> Optional[str]:
        if self._client:
            try:
                return self._client.get(key)
            except Exception as e:
                print(f"获取缓存失败: {e}")
        return None

    def delete_cache(self, key: str):
        if self._client:
            try:
                self._client.delete(key)
            except Exception as e:
                print(f"删除缓存失败: {e}")

    def close(self):
        if self._client:
            self._client.close()
            self._client = None