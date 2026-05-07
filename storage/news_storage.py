import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from core.sqlite_client import SQLiteClient


class NewsStorage:
    def __init__(self, config):
        self._sqlite_client = SQLiteClient(config)

    def save_news(self, news_data: Dict[str, Any]) -> bool:
        return self._sqlite_client.insert_news(news_data)

    def batch_save_news(self, news_list: List[Dict[str, Any]]) -> int:
        return self._sqlite_client.batch_insert_news(news_list)

    def get_news_by_url(self, url: str) -> Optional[Dict]:
        return self._sqlite_client.get_news_by_url(url)

    def get_news_by_source(self, source_name: str, limit: int = 100, offset: int = 0) -> List[Dict]:
        return self._sqlite_client.get_news_by_source(source_name, limit, offset)

    def get_latest_news(self, source_name: str) -> Optional[Dict]:
        return self._sqlite_client.get_latest_news(source_name)

    def search_news(self, keyword: str, source_name: str = None, limit: int = 100) -> List[Dict]:
        return self._sqlite_client.search_news(keyword, source_name, limit)

    def get_statistics(self) -> Dict:
        return self._sqlite_client.get_statistics()

    def delete_news(self, news_id: int) -> bool:
        return self._sqlite_client.delete_news(news_id)

    def update_news(self, news_id: int, update_data: Dict[str, Any]) -> bool:
        return self._sqlite_client.update_news(news_id, update_data)