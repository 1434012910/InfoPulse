import json
from typing import Dict, List, Any, Optional
from core.sqlite_client import SQLiteClient


class ConfigStorage:
    def __init__(self, config):
        self._sqlite_client = SQLiteClient(config)

    def save_source_config(self, name: str, config_data: Dict[str, Any], enabled: bool = True):
        config_json = json.dumps(config_data, ensure_ascii=False)
        self._sqlite_client.save_source_config(name, config_json, enabled)

    def get_source_config(self, name: str) -> Optional[Dict]:
        config = self._sqlite_client.get_source_config(name)
        if config and 'config_json' in config:
            config['config'] = json.loads(config['config_json'])
        return config

    def get_all_source_configs(self) -> List[Dict]:
        configs = self._sqlite_client.get_all_source_configs()
        for config in configs:
            if 'config_json' in config:
                config['config'] = json.loads(config['config_json'])
        return configs

    def delete_source_config(self, name: str) -> bool:
        return self._sqlite_client.delete_source_config(name)

    def update_source_config(self, name: str, config_data: Dict[str, Any], enabled: bool = True):
        config_json = json.dumps(config_data, ensure_ascii=False)
        self._sqlite_client.save_source_config(name, config_json, enabled)

    def enable_source(self, name: str) -> bool:
        config = self.get_source_config(name)
        if config:
            self.update_source_config(name, config['config'], True)
            return True
        return False

    def disable_source(self, name: str) -> bool:
        config = self.get_source_config(name)
        if config:
            self.update_source_config(name, config['config'], False)
            return True
        return False