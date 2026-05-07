import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime


class SQLiteClient:
    _instance = None
    _connection = None
    _cursor = None

    def __new__(cls, config=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config=None):
        if self._connection is None and config:
            self._connect(config)

    def _connect(self, config: Dict[str, Any]):
        sqlite_config = config.get('sqlite', {})
        db_path = sqlite_config.get('path', 'data/news.db')

        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        try:
            self._connection = sqlite3.connect(db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            self._cursor = self._connection.cursor()
            self._init_tables()
        except sqlite3.Error as e:
            print(f"SQLite连接失败: {e}")
            self._connection = None
            self._cursor = None

    def _init_tables(self):
        if not self._cursor:
            return

        self._cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                content TEXT,
                summary TEXT,
                author TEXT,
                source TEXT,
                publish_time DATETIME,
                image_urls TEXT,
                category TEXT,
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                fingerprint TEXT UNIQUE,
                is_incremental BOOLEAN DEFAULT 0
            )
        ''')

        self._cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawl_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT NOT NULL,
                task_id TEXT,
                status TEXT NOT NULL,
                message TEXT,
                crawl_count INTEGER DEFAULT 0,
                duration REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self._cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT UNIQUE NOT NULL,
                last_crawl_time DATETIME,
                last_success_time DATETIME,
                last_error_time DATETIME,
                consecutive_failures INTEGER DEFAULT 0,
                total_success INTEGER DEFAULT 0,
                total_failure INTEGER DEFAULT 0,
                is_running BOOLEAN DEFAULT 0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self._cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                config_json TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self._connection.commit()

    def insert_news(self, news_data: Dict[str, Any]) -> bool:
        if not self._cursor:
            return False

        try:
            self._cursor.execute('''
                INSERT OR IGNORE INTO news 
                (source_name, title, url, content, summary, author, source, 
                 publish_time, image_urls, category, tags, fingerprint, is_incremental)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                news_data.get('source_name'),
                news_data.get('title'),
                news_data.get('url'),
                news_data.get('content'),
                news_data.get('summary'),
                news_data.get('author'),
                news_data.get('source'),
                news_data.get('publish_time'),
                news_data.get('image_urls'),
                news_data.get('category'),
                news_data.get('tags'),
                news_data.get('fingerprint'),
                news_data.get('is_incremental', False)
            ))
            self._connection.commit()
            return self._cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False
        except sqlite3.Error as e:
            print(f"插入新闻失败: {e}")
            return False

    def batch_insert_news(self, news_list: List[Dict[str, Any]]) -> int:
        if not self._cursor:
            return 0

        success_count = 0
        try:
            for news_data in news_list:
                if self.insert_news(news_data):
                    success_count += 1
            return success_count
        except Exception as e:
            print(f"批量插入新闻失败: {e}")
            return success_count

    def get_news_by_url(self, url: str) -> Optional[Dict]:
        if not self._cursor:
            return None

        try:
            self._cursor.execute('SELECT * FROM news WHERE url = ?', (url,))
            row = self._cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"查询新闻失败: {e}")
            return None

    def get_news_by_source(self, source_name: str, limit: int = 100, offset: int = 0) -> List[Dict]:
        if not self._cursor:
            return []

        try:
            self._cursor.execute('''
                SELECT * FROM news 
                WHERE source_name = ? 
                ORDER BY publish_time DESC 
                LIMIT ? OFFSET ?
            ''', (source_name, limit, offset))
            return [dict(row) for row in self._cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"查询新闻失败: {e}")
            return []

    def get_latest_news(self, source_name: str) -> Optional[Dict]:
        if not self._cursor:
            return None

        try:
            self._cursor.execute('''
                SELECT * FROM news 
                WHERE source_name = ? 
                ORDER BY publish_time DESC 
                LIMIT 1
            ''', (source_name,))
            row = self._cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"查询最新新闻失败: {e}")
            return None

    def log_crawl(self, source_name: str, task_id: str, status: str, message: str, 
                  crawl_count: int = 0, duration: float = 0):
        if not self._cursor:
            return

        try:
            self._cursor.execute('''
                INSERT INTO crawl_logs 
                (source_name, task_id, status, message, crawl_count, duration)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (source_name, task_id, status, message, crawl_count, duration))
            self._connection.commit()
        except sqlite3.Error as e:
            print(f"记录采集日志失败: {e}")

    def get_crawl_logs(self, source_name: str = None, limit: int = 100) -> List[Dict]:
        if not self._cursor:
            return []

        try:
            if source_name:
                self._cursor.execute('''
                    SELECT * FROM crawl_logs 
                    WHERE source_name = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (source_name, limit))
            else:
                self._cursor.execute('''
                    SELECT * FROM crawl_logs 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
            return [dict(row) for row in self._cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"查询采集日志失败: {e}")
            return []

    def update_task_status(self, source_name: str, **kwargs):
        if not self._cursor:
            return

        try:
            self._cursor.execute('SELECT id FROM task_status WHERE source_name = ?', (source_name,))
            row = self._cursor.fetchone()

            if row:
                set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
                values = list(kwargs.values()) + [source_name]
                self._cursor.execute(f'''
                    UPDATE task_status 
                    SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                    WHERE source_name = ?
                ''', values)
            else:
                kwargs['source_name'] = source_name
                columns = ', '.join(kwargs.keys())
                placeholders = ', '.join(['?'] * len(kwargs))
                self._cursor.execute(f'''
                    INSERT INTO task_status ({columns})
                    VALUES ({placeholders})
                ''', list(kwargs.values()))

            self._connection.commit()
        except sqlite3.Error as e:
            print(f"更新任务状态失败: {e}")

    def get_task_status(self, source_name: str) -> Optional[Dict]:
        if not self._cursor:
            return None

        try:
            self._cursor.execute('SELECT * FROM task_status WHERE source_name = ?', (source_name,))
            row = self._cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"查询任务状态失败: {e}")
            return None

    def get_all_task_status(self) -> List[Dict]:
        if not self._cursor:
            return []

        try:
            self._cursor.execute('SELECT * FROM task_status ORDER BY source_name')
            return [dict(row) for row in self._cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"查询所有任务状态失败: {e}")
            return []

    def save_source_config(self, name: str, config_json: str, enabled: bool = True):
        if not self._cursor:
            return

        try:
            self._cursor.execute('''
                INSERT OR REPLACE INTO sources_config 
                (name, config_json, enabled, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (name, config_json, enabled))
            self._connection.commit()
        except sqlite3.Error as e:
            print(f"保存采集源配置失败: {e}")

    def get_source_config(self, name: str) -> Optional[Dict]:
        if not self._cursor:
            return None

        try:
            self._cursor.execute('SELECT * FROM sources_config WHERE name = ?', (name,))
            row = self._cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"查询采集源配置失败: {e}")
            return None

    def get_all_source_configs(self) -> List[Dict]:
        if not self._cursor:
            return []

        try:
            self._cursor.execute('SELECT * FROM sources_config ORDER BY name')
            return [dict(row) for row in self._cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"查询所有采集源配置失败: {e}")
            return []

    def delete_source_config(self, name: str) -> bool:
        if not self._cursor:
            return False

        try:
            self._cursor.execute('DELETE FROM sources_config WHERE name = ?', (name,))
            self._connection.commit()
            return self._cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"删除采集源配置失败: {e}")
            return False

    def get_statistics(self) -> Dict:
        if not self._cursor:
            return {}

        try:
            stats = {}

            self._cursor.execute('SELECT COUNT(*) FROM news')
            stats['total_news'] = self._cursor.fetchone()[0]

            self._cursor.execute('SELECT COUNT(DISTINCT source_name) FROM news')
            stats['total_sources'] = self._cursor.fetchone()[0]

            self._cursor.execute('''
                SELECT source_name, COUNT(*) as count 
                FROM news 
                GROUP BY source_name 
                ORDER BY count DESC
            ''')
            stats['news_by_source'] = {row[0]: row[1] for row in self._cursor.fetchall()}

            self._cursor.execute('''
                SELECT COUNT(*) FROM news 
                WHERE created_at >= datetime('now', '-1 day')
            ''')
            stats['news_today'] = self._cursor.fetchone()[0]

            return stats
        except sqlite3.Error as e:
            print(f"获取统计信息失败: {e}")
            return {}

    def search_news(self, keyword: str, source_name: str = None, limit: int = 100) -> List[Dict]:
        if not self._cursor:
            return []

        try:
            if source_name:
                self._cursor.execute('''
                    SELECT * FROM news 
                    WHERE source_name = ? AND (title LIKE ? OR content LIKE ?)
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (source_name, f'%{keyword}%', f'%{keyword}%', limit))
            else:
                self._cursor.execute('''
                    SELECT * FROM news 
                    WHERE title LIKE ? OR content LIKE ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (f'%{keyword}%', f'%{keyword}%', limit))
            return [dict(row) for row in self._cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"搜索新闻失败: {e}")
            return []

    def delete_news(self, news_id: int) -> bool:
        if not self._cursor:
            return False

        try:
            self._cursor.execute('DELETE FROM news WHERE id = ?', (news_id,))
            self._connection.commit()
            return self._cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"删除新闻失败: {e}")
            return False

    def update_news(self, news_id: int, update_data: Dict[str, Any]) -> bool:
        if not self._cursor:
            return False

        try:
            set_clause = ', '.join([f"{k} = ?" for k in update_data.keys()])
            values = list(update_data.values()) + [news_id]
            self._cursor.execute(f'''
                UPDATE news 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', values)
            self._connection.commit()
            return self._cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"更新新闻失败: {e}")
            return False

    def get_logs_by_status(self, status: str, limit: int = 100) -> List[Dict]:
        if not self._cursor:
            return []

        try:
            self._cursor.execute('''
                SELECT * FROM crawl_logs 
                WHERE status = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (status, limit))
            return [dict(row) for row in self._cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"查询日志失败: {e}")
            return []

    def get_logs_by_time_range(self, start_time: str, end_time: str, limit: int = 100) -> List[Dict]:
        if not self._cursor:
            return []

        try:
            self._cursor.execute('''
                SELECT * FROM crawl_logs 
                WHERE created_at BETWEEN ? AND ?
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (start_time, end_time, limit))
            return [dict(row) for row in self._cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"查询日志失败: {e}")
            return []

    def clear_old_logs(self, days: int = 30):
        if not self._cursor:
            return

        try:
            self._cursor.execute('''
                DELETE FROM crawl_logs 
                WHERE created_at < datetime('now', ?)
            ''', (f'-{days} days',))
            self._connection.commit()
        except sqlite3.Error as e:
            print(f"清理旧日志失败: {e}")

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None
            self._cursor = None