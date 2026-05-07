import time
import threading
from typing import Dict
from collections import defaultdict


class RateLimiter:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._last_request_time = defaultdict(float)
            self._request_counts = defaultdict(int)
            self._window_start = defaultdict(float)
            self._initialized = True

    def wait_if_needed(self, source_name: str, interval: float):
        with self._lock:
            current_time = time.time()
            last_time = self._last_request_time.get(source_name, 0)
            elapsed = current_time - last_time

            if elapsed < interval:
                wait_time = interval - elapsed
                time.sleep(wait_time)

            self._last_request_time[source_name] = time.time()

    def check_rate_limit(self, source_name: str, max_requests: int, window: float) -> bool:
        with self._lock:
            current_time = time.time()
            window_start = self._window_start.get(source_name, 0)

            if current_time - window_start > window:
                self._window_start[source_name] = current_time
                self._request_counts[source_name] = 0

            if self._request_counts[source_name] >= max_requests:
                return False

            self._request_counts[source_name] += 1
            return True

    def get_wait_time(self, source_name: str, interval: float) -> float:
        current_time = time.time()
        last_time = self._last_request_time.get(source_name, 0)
        elapsed = current_time - last_time

        if elapsed < interval:
            return interval - elapsed
        return 0

    def reset(self, source_name: str):
        with self._lock:
            self._last_request_time.pop(source_name, None)
            self._request_counts.pop(source_name, None)
            self._window_start.pop(source_name, None)

    def reset_all(self):
        with self._lock:
            self._last_request_time.clear()
            self._request_counts.clear()
            self._window_start.clear()