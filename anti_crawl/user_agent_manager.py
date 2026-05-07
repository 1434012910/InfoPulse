import random
import threading
from typing import List


class UserAgentManager:
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
            self._user_agents = config.get('crawler', {}).get('user_agents', [])
            if not self._user_agents:
                self._user_agents = self._get_default_user_agents()
            self._initialized = True

    def _get_default_user_agents(self) -> List[str]:
        return [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        ]

    def get_random_user_agent(self) -> str:
        if not self._user_agents:
            return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        return random.choice(self._user_agents)

    def get_mobile_user_agent(self) -> str:
        mobile_agents = [
            ua for ua in self._user_agents 
            if 'Mobile' in ua or 'Android' in ua or 'iPhone' in ua or 'iPad' in ua
        ]
        if mobile_agents:
            return random.choice(mobile_agents)
        return self.get_random_user_agent()

    def get_desktop_user_agent(self) -> str:
        desktop_agents = [
            ua for ua in self._user_agents 
            if 'Mobile' not in ua and 'Android' not in ua and 'iPhone' not in ua and 'iPad' not in ua
        ]
        if desktop_agents:
            return random.choice(desktop_agents)
        return self.get_random_user_agent()

    def add_user_agent(self, user_agent: str):
        with self._lock:
            if user_agent not in self._user_agents:
                self._user_agents.append(user_agent)

    def remove_user_agent(self, user_agent: str):
        with self._lock:
            if user_agent in self._user_agents:
                self._user_agents.remove(user_agent)

    def get_user_agents_count(self) -> int:
        return len(self._user_agents)

    def clear_user_agents(self):
        with self._lock:
            self._user_agents.clear()

    def reset_to_default(self):
        with self._lock:
            self._user_agents = self._get_default_user_agents()