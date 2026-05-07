import random
import requests
import threading
from typing import List, Optional, Dict
from collections import deque


class ProxyManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, config=None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config=None):
        if config and not hasattr(self, '_initialized'):
            self._config = config
            self._proxy_config = config.get('crawler', {}).get('proxy', {})
            self._proxy_pool_url = self._proxy_config.get('proxy_pool_url', '')
            self._proxy_list = deque(self._proxy_config.get('proxy_list', []))
            self._failed_proxies = set()
            self._initialized = True

    def get_proxy(self) -> Optional[str]:
        if not self._proxy_config.get('enabled', False):
            return None

        if self._proxy_pool_url:
            return self._fetch_proxy_from_pool()

        if self._proxy_list:
            return self._get_from_list()

        return None

    def _fetch_proxy_from_pool(self) -> Optional[str]:
        try:
            response = requests.get(self._proxy_pool_url, timeout=5)
            if response.status_code == 200:
                proxy = response.text.strip()
                if proxy and proxy not in self._failed_proxies:
                    return proxy
        except Exception:
            pass
        return None

    def _get_from_list(self) -> Optional[str]:
        available_proxies = [p for p in self._proxy_list if p not in self._failed_proxies]
        if not available_proxies:
            self._failed_proxies.clear()
            available_proxies = list(self._proxy_list)

        if available_proxies:
            return random.choice(available_proxies)
        return None

    def report_failed(self, proxy: str):
        with self._lock:
            self._failed_proxies.add(proxy)

    def report_success(self, proxy: str):
        with self._lock:
            self._failed_proxies.discard(proxy)

    def add_proxy(self, proxy: str):
        with self._lock:
            if proxy not in self._proxy_list:
                self._proxy_list.append(proxy)

    def remove_proxy(self, proxy: str):
        with self._lock:
            if proxy in self._proxy_list:
                self._proxy_list.remove(proxy)
            self._failed_proxies.discard(proxy)

    def get_proxies_dict(self, proxy: str) -> Dict[str, str]:
        if not proxy:
            return {}
        return {
            'http': proxy,
            'https': proxy
        }

    def test_proxy(self, proxy: str, test_url: str = 'http://httpbin.org/ip') -> bool:
        try:
            response = requests.get(
                test_url,
                proxies=self.get_proxies_dict(proxy),
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_available_count(self) -> int:
        return len([p for p in self._proxy_list if p not in self._failed_proxies])

    def get_failed_count(self) -> int:
        return len(self._failed_proxies)

    def clear_failed(self):
        with self._lock:
            self._failed_proxies.clear()

    def reset(self):
        with self._lock:
            self._failed_proxies.clear()