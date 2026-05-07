import time
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from core.config import Config
from core.logger import Logger
from collectors.collector_factory import CollectorFactory
from anti_crawl.rate_limiter import RateLimiter


class TaskScheduler:
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
            self._logger = Logger.get_logger('scheduler', config.to_dict())
            self._scheduler = BackgroundScheduler(
                timezone=config.get_scheduler_config().get('timezone', 'Asia/Shanghai')
            )
            self._collectors = {}
            self._tasks = {}
            self._running = False
            self._rate_limiter = RateLimiter()
            self._initialized = True

    def _load_sources(self, sources_config_path: str):
        try:
            collectors = CollectorFactory.create_from_config_file(sources_config_path, self._config)
            for collector in collectors:
                source_name = collector.source_name
                self._collectors[source_name] = collector
                self._logger.info(f"加载采集源: {source_name}")
        except Exception as e:
            self._logger.error(f"加载采集源配置失败: {e}")

    def _add_job(self, source_name: str, interval: int):
        if source_name in self._tasks:
            self._remove_job(source_name)

        try:
            job = self._scheduler.add_job(
                self._execute_task,
                trigger=IntervalTrigger(seconds=interval),
                args=[source_name],
                id=f'task_{source_name}',
                name=f'采集任务-{source_name}',
                replace_existing=True,
                max_instances=1,
                misfire_grace_time=60
            )
            self._tasks[source_name] = {
                'job': job,
                'interval': interval,
                'last_run': None,
                'next_run': job.next_run_time,
                'status': 'scheduled'
            }
            self._logger.info(f"添加定时任务: {source_name}, 间隔: {interval}秒")
        except Exception as e:
            self._logger.error(f"添加定时任务失败: {source_name}, 错误: {e}")

    def _remove_job(self, source_name: str):
        if source_name in self._tasks:
            try:
                self._scheduler.remove_job(f'task_{source_name}')
                del self._tasks[source_name]
                self._logger.info(f"移除定时任务: {source_name}")
            except Exception as e:
                self._logger.error(f"移除定时任务失败: {source_name}, 错误: {e}")

    def _execute_task(self, source_name: str):
        if source_name not in self._collectors:
            self._logger.error(f"采集源不存在: {source_name}")
            return

        collector = self._collectors[source_name]
        interval = self._tasks.get(source_name, {}).get('interval', 60)

        self._rate_limiter.wait_if_needed(source_name, interval)

        self._logger.info(f"开始执行采集任务: {source_name}")
        self._tasks[source_name]['status'] = 'running'
        self._tasks[source_name]['last_run'] = datetime.now()

        try:
            success = collector.collect()
            if success:
                self._tasks[source_name]['status'] = 'completed'
                self._logger.info(f"采集任务完成: {source_name}")
            else:
                self._tasks[source_name]['status'] = 'failed'
                self._logger.warning(f"采集任务失败: {source_name}")
        except Exception as e:
            self._tasks[source_name]['status'] = 'error'
            self._logger.error(f"采集任务异常: {source_name}, 错误: {e}")

    def start(self, sources_config_path: str = None):
        if self._running:
            self._logger.warning("调度器已在运行中")
            return

        if sources_config_path is None:
            sources_config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'config', 'sources.json'
            )

        self._load_sources(sources_config_path)

        for source_name, collector in self._collectors.items():
            interval = collector.source_config.get('interval', 60)
            self._add_job(source_name, interval)

        self._scheduler.start()
        self._running = True
        self._logger.info("调度器启动成功")

    def stop(self):
        if not self._running:
            return

        self._scheduler.shutdown()
        self._running = False
        self._tasks.clear()
        self._logger.info("调度器已停止")

    def pause_task(self, source_name: str):
        if source_name in self._tasks:
            try:
                self._scheduler.pause_job(f'task_{source_name}')
                self._tasks[source_name]['status'] = 'paused'
                self._logger.info(f"暂停任务: {source_name}")
            except Exception as e:
                self._logger.error(f"暂停任务失败: {source_name}, 错误: {e}")

    def resume_task(self, source_name: str):
        if source_name in self._tasks:
            try:
                self._scheduler.resume_job(f'task_{source_name}')
                self._tasks[source_name]['status'] = 'scheduled'
                self._logger.info(f"恢复任务: {source_name}")
            except Exception as e:
                self._logger.error(f"恢复任务失败: {source_name}, 错误: {e}")

    def run_task_now(self, source_name: str):
        if source_name in self._collectors:
            thread = threading.Thread(target=self._execute_task, args=(source_name,))
            thread.start()
            self._logger.info(f"手动触发任务: {source_name}")

    def get_task_status(self, source_name: str) -> Optional[Dict]:
        if source_name in self._tasks:
            task_info = self._tasks[source_name].copy()
            task_info['collector_status'] = self._collectors[source_name].get_status()
            return task_info
        return None

    def get_all_tasks_status(self) -> List[Dict]:
        tasks = []
        for source_name, task_info in self._tasks.items():
            status = task_info.copy()
            status['source_name'] = source_name
            status['collector_status'] = self._collectors[source_name].get_status()
            tasks.append(status)
        return tasks

    def get_running_tasks(self) -> List[str]:
        return [name for name, info in self._tasks.items() if info['status'] == 'running']

    def is_running(self) -> bool:
        return self._running

    def get_collectors(self) -> Dict:
        return self._collectors.copy()

    def reload_config(self, sources_config_path: str = None):
        self.stop()
        self._collectors.clear()
        self._tasks.clear()
        self.start(sources_config_path)