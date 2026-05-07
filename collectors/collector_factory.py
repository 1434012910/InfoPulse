from typing import Dict, Any, Optional
from core.config import Config
from .base_collector import BaseCollector
from .app_reverse_collector import AppReverseCollector
from .app_direct_collector import AppDirectCollector
from .web_reverse_collector import WebReverseCollector
from .web_static_collector import WebStaticCollector
from .web_direct_collector import WebDirectCollector


class CollectorFactory:
    _collectors = {
        ('app', 'reverse'): AppReverseCollector,
        ('app', 'direct'): AppDirectCollector,
        ('web', 'reverse'): WebReverseCollector,
        ('web', 'static'): WebStaticCollector,
        ('web', 'direct'): WebDirectCollector,
    }

    @classmethod
    def register_collector(cls, source_type: str, method: str, collector_class: type):
        if not issubclass(collector_class, BaseCollector):
            raise TypeError(f"采集器类必须继承自BaseCollector")
        cls._collectors[(source_type, method)] = collector_class

    @classmethod
    def create_collector(cls, source_config: Dict[str, Any], config: Config) -> Optional[BaseCollector]:
        source_type = source_config.get('type', '').lower()
        method = source_config.get('method', '').lower()

        collector_class = cls._collectors.get((source_type, method))
        if not collector_class:
            raise ValueError(f"未找到对应的采集器类型: type={source_type}, method={method}")

        return collector_class(source_config, config)

    @classmethod
    def get_supported_types(cls):
        return list(cls._collectors.keys())

    @classmethod
    def create_from_config_file(cls, config_path: str, config: Config):
        import json
        import os

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            sources_config = json.load(f)

        collectors = []
        for source_config in sources_config.get('sources', []):
            if source_config.get('enabled', True):
                try:
                    collector = cls.create_collector(source_config, config)
                    collectors.append(collector)
                except Exception as e:
                    print(f"创建采集器失败: {source_config.get('name')}, 错误: {e}")

        return collectors