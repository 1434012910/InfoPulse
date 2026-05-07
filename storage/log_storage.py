from typing import Dict, List, Any, Optional
from core.sqlite_client import SQLiteClient


class LogStorage:
    def __init__(self, config):
        self._sqlite_client = SQLiteClient(config)

    def log_crawl(self, source_name: str, task_id: str, status: str, message: str, 
                  crawl_count: int = 0, duration: float = 0):
        self._sqlite_client.log_crawl(source_name, task_id, status, message, crawl_count, duration)

    def get_crawl_logs(self, source_name: str = None, limit: int = 100) -> List[Dict]:
        return self._sqlite_client.get_crawl_logs(source_name, limit)

    def get_logs_by_status(self, status: str, limit: int = 100) -> List[Dict]:
        return self._sqlite_client.get_logs_by_status(status, limit)

    def get_logs_by_time_range(self, start_time: str, end_time: str, limit: int = 100) -> List[Dict]:
        return self._sqlite_client.get_logs_by_time_range(start_time, end_time, limit)

    def clear_old_logs(self, days: int = 30):
        self._sqlite_client.clear_old_logs(days)