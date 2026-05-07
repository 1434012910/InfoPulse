import os
import sys
import argparse
import signal
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from core.config import Config
from core.logger import Logger
from scheduler.task_manager import TaskManager
from web_admin.app import create_app


def main():
    parser = argparse.ArgumentParser(description='InfoPulse 资讯采集框架')
    parser.add_argument('--mode', choices=['scheduler', 'web', 'all'], default='all',
                       help='运行模式: scheduler=仅调度器, web=仅Web管理, all=全部')
    parser.add_argument('--config', default=None, help='主配置文件路径')
    parser.add_argument('--sources', default=None, help='采集源配置文件路径')
    parser.add_argument('--host', default='0.0.0.0', help='Web管理界面监听地址')
    parser.add_argument('--port', type=int, default=5000, help='Web管理界面端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')

    args = parser.parse_args()

    config_path = args.config or os.path.join(os.path.dirname(__file__), 'config', 'config.json')
    sources_path = args.sources or os.path.join(os.path.dirname(__file__), 'config', 'sources.json')

    config = Config(config_path)
    logger = Logger.get_logger('main', config.to_dict())

    logger.info('='*50)
    logger.info('InfoPulse 资讯采集框架启动')
    logger.info(f'启动时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    logger.info(f'运行模式: {args.mode}')
    logger.info('='*50)

    task_manager = TaskManager(config)

    def signal_handler(signum, frame):
        logger.info('收到终止信号，正在停止...')
        task_manager.stop_scheduler()
        logger.info('程序已退出')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.mode in ['scheduler', 'all']:
        logger.info('启动调度器...')
        task_manager.start_scheduler(sources_path)
        logger.info('调度器启动完成')

    if args.mode in ['web', 'all']:
        logger.info('启动Web管理界面...')
        app = create_app(config_path)
        
        web_config = config.get_web_admin_config()
        host = args.host or web_config.get('host', '0.0.0.0')
        port = args.port or web_config.get('port', 5000)
        debug = args.debug or web_config.get('debug', False)

        logger.info(f'Web管理界面: http://{host}:{port}')
        
        if args.mode == 'all':
            web_thread = threading.Thread(
                target=lambda: app.run(host=host, port=port, debug=debug, use_reloader=False),
                daemon=True
            )
            web_thread.start()
            logger.info('Web管理界面已在后台启动')
        else:
            app.run(host=host, port=port, debug=debug)

    if args.mode == 'all':
        logger.info('所有服务已启动，按 Ctrl+C 退出')
        try:
            while True:
                signal.pause()
        except (KeyboardInterrupt, SystemExit):
            pass


if __name__ == '__main__':
    main()