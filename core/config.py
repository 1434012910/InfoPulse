import json
import os
from typing import Dict, Any, Optional


class Config:
    _instance = None
    _config = None

    def __new__(cls, config_path=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path=None):
        if self._config is None:
            self._load_config(config_path)

    def _load_config(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.json')

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = json.load(f)

    def get(self, key: str, default=None) -> Any:
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def reload(self, config_path=None):
        self._config = None
        self._load_config(config_path)

    def get_redis_config(self) -> Dict:
        return self.get('redis', {})

    def get_sqlite_config(self) -> Dict:
        return self.get('sqlite', {})

    def get_logging_config(self) -> Dict:
        return self.get('logging', {})

    def get_alert_config(self) -> Dict:
        return self.get('alert', {})

    def get_crawler_config(self) -> Dict:
        return self.get('crawler', {})

    def get_dedup_config(self) -> Dict:
        return self.get('dedup', {})

    def get_web_admin_config(self) -> Dict:
        return self.get('web_admin', {})

    def get_scheduler_config(self) -> Dict:
        return self.get('scheduler', {})

    def to_dict(self) -> Dict:
        return self._config.copy()