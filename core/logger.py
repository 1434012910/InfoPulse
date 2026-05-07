import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


class Logger:
    _loggers = {}

    @classmethod
    def get_logger(cls, name='infopulse', config=None):
        if name in cls._loggers:
            return cls._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        if not logger.handlers:
            if config:
                cls._setup_handlers(logger, config)
            else:
                cls._setup_default_handlers(logger)

        cls._loggers[name] = logger
        return logger

    @classmethod
    def _setup_handlers(cls, logger, config):
        log_config = config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('file', 'logs/infopulse.log')
        max_size = log_config.get('max_size', 10 * 1024 * 1024)
        backup_count = log_config.get('backup_count', 5)
        log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        formatter = logging.Formatter(log_format)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    @classmethod
    def _setup_default_handlers(cls, logger):
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    @classmethod
    def log_task_start(cls, logger, source_name, task_id=None):
        logger.info(f"任务开始 - 采集源: {source_name}, 任务ID: {task_id or 'N/A'}")

    @classmethod
    def log_task_end(cls, logger, source_name, success=True, count=0, task_id=None):
        status = "成功" if success else "失败"
        logger.info(f"任务结束 - 采集源: {source_name}, 状态: {status}, 采集数量: {count}, 任务ID: {task_id or 'N/A'}")

    @classmethod
    def log_task_error(cls, logger, source_name, error, task_id=None):
        logger.error(f"任务异常 - 采集源: {source_name}, 错误: {error}, 任务ID: {task_id or 'N/A'}")

    @classmethod
    def log_dedup_hit(cls, logger, source_name, url):
        logger.debug(f"去重命中 - 采集源: {source_name}, URL: {url}")

    @classmethod
    def log_dedup_miss(cls, logger, source_name, url):
        logger.debug(f"去重未命中 - 采集源: {source_name}, URL: {url}")

    @classmethod
    def log_reverse_alert(cls, logger, source_name, js_file, error):
        logger.warning(f"逆向失效告警 - 采集源: {source_name}, JS文件: {js_file}, 错误: {error}")

    @classmethod
    def log_performance(cls, logger, source_name, duration, count):
        logger.info(f"性能指标 - 采集源: {source_name}, 耗时: {duration:.2f}秒, 采集数量: {count}")

    @classmethod
    def log_proxy_switch(cls, logger, source_name, old_proxy, new_proxy):
        logger.info(f"代理切换 - 采集源: {source_name}, 旧代理: {old_proxy}, 新代理: {new_proxy}")

    @classmethod
    def log_retry(cls, logger, source_name, attempt, max_retries, error):
        logger.warning(f"重试中 - 采集源: {source_name}, 第{attempt}/{max_retries}次, 错误: {error}")