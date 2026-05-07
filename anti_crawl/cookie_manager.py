import json
import os
import threading
from typing import Dict, Optional
from datetime import datetime, timedelta


class CookieManager:
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
            self._cookies = {}
            self._cookie_expiry = {}
            self._cookie_file = 'data/cookies.json'
            self._load_cookies()
            self._initialized = True

    def _load_cookies(self):
        if os.path.exists(self._cookie_file):
            try:
                with open(self._cookie_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._cookies = data.get('cookies', {})
                    self._cookie_expiry = data.get('expiry', {})
            except Exception:
                self._cookies = {}
                self._cookie_expiry = {}

    def _save_cookies(self):
        try:
            os.makedirs(os.path.dirname(self._cookie_file), exist_ok=True)
            with open(self._cookie_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'cookies': self._cookies,
                    'expiry': self._cookie_expiry
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_cookies(self, source_name: str) -> Dict:
        if source_name not in self._cookies:
            return {}

        expiry_str = self._cookie_expiry.get(source_name)
        if expiry_str:
            try:
                expiry = datetime.fromisoformat(expiry_str)
                if datetime.now() > expiry:
                    del self._cookies[source_name]
                    del self._cookie_expiry[source_name]
                    self._save_cookies()
                    return {}
            except Exception:
                pass

        return self._cookies[source_name]

    def set_cookies(self, source_name: str, cookies: Dict, expiry_hours: int = 24):
        with self._lock:
            self._cookies[source_name] = cookies
            self._cookie_expiry[source_name] = (
                datetime.now() + timedelta(hours=expiry_hours)
            ).isoformat()
            self._save_cookies()

    def update_cookies(self, source_name: str, new_cookies: Dict):
        with self._lock:
            if source_name in self._cookies:
                self._cookies[source_name].update(new_cookies)
            else:
                self._cookies[source_name] = new_cookies
            self._save_cookies()

    def clear_cookies(self, source_name: str):
        with self._lock:
            self._cookies.pop(source_name, None)
            self._cookie_expiry.pop(source_name, None)
            self._save_cookies()

    def clear_all_cookies(self):
        with self._lock:
            self._cookies.clear()
            self._cookie_expiry.clear()
            self._save_cookies()

    def has_valid_cookies(self, source_name: str) -> bool:
        if source_name not in self._cookies:
            return False

        expiry_str = self._cookie_expiry.get(source_name)
        if expiry_str:
            try:
                expiry = datetime.fromisoformat(expiry_str)
                return datetime.now() <= expiry
            except Exception:
                return False
        return True

    def get_all_sources(self):
        return list(self._cookies.keys())