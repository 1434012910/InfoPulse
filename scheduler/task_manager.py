import threading
from typing import Dict, List, Any, Optional
from datetime import datetime

from core.config import Config
from core.logger import Logger
from core.sqlite_client import SQLiteClient
from .task_scheduler import TaskScheduler


class TaskManager:
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
            self._logger = Logger.get_logger('task_manager', config.to_dict())
            self._sqlite_client = SQLiteClient(config)
            self._scheduler = TaskScheduler(config)
            self._initialized = True

    def start_scheduler(self, sources_config_path: str = None):
        self._scheduler.start(sources_config_path)
        self._logger.info("任务管理器启动")

    def stop_scheduler(self):
        self._scheduler.stop()
        self._logger.info("任务管理器停止")

    def get_all_tasks(self) -> List[Dict]:
        return self._scheduler.get_all_tasks_status()

    def get_task_detail(self, source_name: str) -> Optional[Dict]:
        task_status = self._scheduler.get_task_status(source_name)
        if task_status:
            task_status['logs'] = self._sqlite_client.get_crawl_logs(source_name, limit=50)
            task_status['news_count'] = len(self._sqlite_client.get_news_by_source(source_name, limit=1000))
        return task_status

    def pause_task(self, source_name: str) -> bool:
        try:
            self._scheduler.pause_task(source_name)
            self._sqlite_client.update_task_status(
                source_name,
                is_running=False,
                status='paused'
            )
            return True
        except Exception as e:
            self._logger.error(f"暂停任务失败: {source_name}, 错误: {e}")
            return False

    def resume_task(self, source_name: str) -> bool:
        try:
            self._scheduler.resume_task(source_name)
            self._sqlite_client.update_task_status(
                source_name,
                status='scheduled'
            )
            return True
        except Exception as e:
            self._logger.error(f"恢复任务失败: {source_name}, 错误: {e}")
            return False

    def run_task_now(self, source_name: str) -> bool:
        try:
            self._scheduler.run_task_now(source_name)
            return True
        except Exception as e:
            self._logger.error(f"手动触发任务失败: {source_name}, 错误: {e}")
            return False

    def get_task_logs(self, source_name: str = None, limit: int = 100) -> List[Dict]:
        return self._sqlite_client.get_crawl_logs(source_name, limit)

    def get_task_statistics(self) -> Dict:
        stats = {
            'total_tasks': len(self._scheduler.get_all_tasks_status()),
            'running_tasks': len(self._scheduler.get_running_tasks()),
            'total_news': 0,
            'news_by_source': {}
        }

        db_stats = self._sqlite_client.get_statistics()
        stats['total_news'] = db_stats.get('total_news', 0)
        stats['news_by_source'] = db_stats.get('news_by_source', {})

        return stats

    def get_source_configs(self) -> List[Dict]:
        return self._sqlite_client.get_all_source_configs()

    def update_source_config(self, name: str, config_data: Dict[str, Any]) -> bool:
        try:
            import json
            config_json = json.dumps(config_data, ensure_ascii=False)
            self._sqlite_client.save_source_config(name, config_json, config_data.get('enabled', True))
            self._scheduler.reload_config()
            return True
        except Exception as e:
            self._logger.error(f"更新采集源配置失败: {name}, 错误: {e}")
            return False

    def delete_source_config(self, name: str) -> bool:
        try:
            self._sqlite_client.delete_source_config(name)
            self._scheduler.reload_config()
            return True
        except Exception as e:
            self._logger.error(f"删除采集源配置失败: {name}, 错误: {e}")
            return False

    def add_source_config(self, config_data: Dict[str, Any]) -> bool:
        try:
            name = config_data.get('name')
            if not name:
                return False

            import json
            config_json = json.dumps(config_data, ensure_ascii=False)
            self._sqlite_client.save_source_config(name, config_json, config_data.get('enabled', True))
            self._scheduler.reload_config()
            return True
        except Exception as e:
            self._logger.error(f"添加采集源配置失败: {config_data.get('name')}, 错误: {e}")
            return False

    def reload_scheduler(self) -> bool:
        try:
            self._scheduler.reload_config()
            return True
        except Exception as e:
            self._logger.error(f"重新加载调度器失败: {e}")
            return False

    def get_system_status(self) -> Dict:
        return {
            'scheduler_running': self._scheduler.is_running(),
            'total_tasks': len(self._scheduler.get_all_tasks_status()),
            'running_tasks': len(self._scheduler.get_running_tasks()),
            'total_news': self._sqlite_client.get_statistics().get('total_news', 0),
            'uptime': datetime.now().isoformat()
        }