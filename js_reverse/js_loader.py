import os
import importlib
from typing import Dict, List, Optional
from core.logger import Logger


class JSLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._js_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'js_reverse')
            self._js_files = {}
            self._logger = Logger.get_logger('js_loader')
            self._scan_js_files()
            self._initialized = True

    def _scan_js_files(self):
        if not os.path.exists(self._js_dir):
            self._logger.warning(f"JS目录不存在: {self._js_dir}")
            return

        for filename in os.listdir(self._js_dir):
            if filename.endswith('.js'):
                file_path = os.path.join(self._js_dir, filename)
                self._js_files[filename] = file_path
                self._logger.debug(f"发现JS文件: {filename}")

    def get_js_file_path(self, filename: str) -> Optional[str]:
        if filename in self._js_files:
            return self._js_files[filename]

        full_path = os.path.join(self._js_dir, filename)
        if os.path.exists(full_path):
            self._js_files[filename] = full_path
            return full_path

        return None

    def get_all_js_files(self) -> Dict[str, str]:
        return self._js_files.copy()

    def get_js_files_list(self) -> List[str]:
        return list(self._js_files.keys())

    def reload_js_files(self):
        self._js_files.clear()
        self._scan_js_files()

    def add_js_file(self, filename: str, content: str) -> bool:
        try:
            file_path = os.path.join(self._js_dir, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self._js_files[filename] = file_path
            self._logger.info(f"JS文件添加成功: {filename}")
            return True
        except Exception as e:
            self._logger.error(f"JS文件添加失败: {filename}, 错误: {e}")
            return False

    def remove_js_file(self, filename: str) -> bool:
        if filename not in self._js_files:
            return False

        try:
            file_path = self._js_files[filename]
            if os.path.exists(file_path):
                os.remove(file_path)
            del self._js_files[filename]
            self._logger.info(f"JS文件删除成功: {filename}")
            return True
        except Exception as e:
            self._logger.error(f"JS文件删除失败: {filename}, 错误: {e}")
            return False

    def update_js_file(self, filename: str, content: str) -> bool:
        if filename in self._js_files:
            return self.add_js_file(filename, content)
        return False

    def get_js_file_content(self, filename: str) -> Optional[str]:
        file_path = self.get_js_file_path(filename)
        if not file_path:
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self._logger.error(f"读取JS文件失败: {filename}, 错误: {e}")
            return None