import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

from core.logger import Logger
from core.config import Config
from core.redis_client import RedisClient
from core.sqlite_client import SQLiteClient


class BaseCollector(ABC):
    def __init__(self, source_config: Dict[str, Any], config: Config):
        self.source_config = source_config
        self.config = config
        self.source_name = source_config.get('name', 'unknown')
        self.logger = Logger.get_logger(f'collector.{self.source_name}', config.to_dict())
        self.redis_client = RedisClient(config.to_dict())
        self.sqlite_client = SQLiteClient(config.to_dict())
        self.task_id = str(uuid.uuid4())[:8]
        self.is_running = False
        self.last_crawl_time = None
        self.consecutive_failures = 0

    @abstractmethod
    def _fetch_data(self) -> Any:
        pass

    @abstractmethod
    def _parse_response(self, response: Any) -> List[Dict[str, Any]]:
        pass

    def _pre_process(self):
        Logger.log_task_start(self.logger, self.source_name, self.task_id)
        self.is_running = True
        self.sqlite_client.update_task_status(
            self.source_name,
            is_running=True,
            last_crawl_time=datetime.now().isoformat()
        )

    def _post_process(self, news_list: List[Dict[str, Any]], success: bool):
        self.is_running = False
        self.last_crawl_time = datetime.now()

        if success:
            self.consecutive_failures = 0
            self.sqlite_client.update_task_status(
                self.source_name,
                is_running=False,
                last_success_time=datetime.now().isoformat(),
                total_success=self._get_task_status().get('total_success', 0) + 1,
                consecutive_failures=0
            )
        else:
            self.consecutive_failures += 1
            self.sqlite_client.update_task_status(
                self.source_name,
                is_running=False,
                last_error_time=datetime.now().isoformat(),
                total_failure=self._get_task_status().get('total_failure', 0) + 1,
                consecutive_failures=self.consecutive_failures
            )

            alert_config = self.config.get_alert_config()
            if (alert_config.get('enabled', False) and 
                self.consecutive_failures >= alert_config.get('failure_threshold', 5)):
                self._trigger_alert(f"采集源 {self.source_name} 连续失败 {self.consecutive_failures} 次")

        Logger.log_task_end(self.logger, self.source_name, success, len(news_list), self.task_id)

    def _get_task_status(self) -> Dict:
        status = self.sqlite_client.get_task_status(self.source_name)
        return status or {}

    def _dedup_check(self, news_item: Dict[str, Any]) -> bool:
        dedup_config = self.config.get_dedup_config()
        fingerprint = self.redis_client.generate_fingerprint(news_item.get('url', ''), 'url')

        if self.redis_client.check_duplicate(fingerprint, self.source_name, dedup_config):
            Logger.log_dedup_hit(self.logger, self.source_name, news_item.get('url', ''))
            return False

        self.redis_client.add_to_bloom_filter(fingerprint, self.source_name, dedup_config)
        Logger.log_dedup_miss(self.logger, self.source_name, news_item.get('url', ''))
        return True

    def _check_incremental(self, news_item: Dict[str, Any]) -> bool:
        if not self.source_config.get('incremental', False):
            return True

        latest_news = self.sqlite_client.get_latest_news(self.source_name)
        if not latest_news:
            return True

        publish_time = news_item.get('publish_time')
        if publish_time and latest_news.get('publish_time'):
            if isinstance(publish_time, str):
                try:
                    publish_time = datetime.fromisoformat(publish_time)
                except:
                    return True

            if isinstance(latest_news['publish_time'], str):
                try:
                    latest_time = datetime.fromisoformat(latest_news['publish_time'])
                except:
                    return True
            else:
                latest_time = latest_news['publish_time']

            return publish_time > latest_time

        return True

    def _save_news(self, news_list: List[Dict[str, Any]]) -> int:
        saved_count = 0
        for news_item in news_list:
            if not self._dedup_check(news_item):
                continue

            if not self._check_incremental(news_item):
                continue

            news_data = {
                'source_name': self.source_name,
                'title': news_item.get('title', ''),
                'url': news_item.get('url', ''),
                'content': news_item.get('content', ''),
                'summary': news_item.get('summary', ''),
                'author': news_item.get('author', ''),
                'source': news_item.get('source', ''),
                'publish_time': news_item.get('publish_time'),
                'image_urls': news_item.get('image_urls', ''),
                'category': news_item.get('category', ''),
                'tags': news_item.get('tags', ''),
                'fingerprint': self.redis_client.generate_fingerprint(news_item.get('url', ''), 'url'),
                'is_incremental': self.source_config.get('incremental', False)
            }

            if self.sqlite_client.insert_news(news_data):
                saved_count += 1

        return saved_count

    def _retry(self, func, *args, **kwargs):
        retry_times = self.source_config.get('retry_times', 3)
        retry_interval = self.source_config.get('retry_interval', 5)

        for attempt in range(1, retry_times + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                Logger.log_retry(self.logger, self.source_name, attempt, retry_times, str(e))
                if attempt < retry_times:
                    time.sleep(retry_interval)
                else:
                    raise

    def _trigger_alert(self, message: str):
        alert_config = self.config.get_alert_config()
        self.logger.warning(f"告警触发: {message}")

        if alert_config.get('wechat', {}).get('webhook_url'):
            self._send_wechat_alert(message, alert_config['wechat'])

        if alert_config.get('email', {}).get('smtp_server'):
            self._send_email_alert(message, alert_config['email'])

    def _send_wechat_alert(self, message: str, wechat_config: Dict):
        pass

    def _send_email_alert(self, message: str, email_config: Dict):
        pass

    def collect(self) -> bool:
        start_time = time.time()
        self._pre_process()

        try:
            response = self._retry(self._fetch_data)
            news_list = self._parse_response(response)
            saved_count = self._save_news(news_list)

            duration = time.time() - start_time
            Logger.log_performance(self.logger, self.source_name, duration, saved_count)

            self.sqlite_client.log_crawl(
                self.source_name,
                self.task_id,
                'success',
                f'成功采集 {saved_count} 条新闻',
                saved_count,
                duration
            )

            self._post_process(news_list, True)
            return True

        except Exception as e:
            Logger.log_task_error(self.logger, self.source_name, str(e), self.task_id)

            self.sqlite_client.log_crawl(
                self.source_name,
                self.task_id,
                'error',
                str(e),
                0,
                time.time() - start_time
            )

            self._post_process([], False)
            return False

    def get_status(self) -> Dict[str, Any]:
        task_status = self._get_task_status()
        return {
            'source_name': self.source_name,
            'is_running': self.is_running,
            'last_crawl_time': self.last_crawl_time.isoformat() if self.last_crawl_time else None,
            'consecutive_failures': self.consecutive_failures,
            'total_success': task_status.get('total_success', 0),
            'total_failure': task_status.get('total_failure', 0)
        }