import execjs
import os
from typing import Any, Optional
from core.logger import Logger


class JSExecutor:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._contexts = {}
            self._logger = Logger.get_logger('js_executor')
            self._initialized = True

    def load_js_file(self, js_file_path: str) -> bool:
        if js_file_path in self._contexts:
            return True

        if not os.path.exists(js_file_path):
            self._logger.error(f"JS文件不存在: {js_file_path}")
            return False

        try:
            with open(js_file_path, 'r', encoding='utf-8') as f:
                js_code = f.read()
            context = execjs.compile(js_code)
            self._contexts[js_file_path] = context
            self._logger.info(f"JS文件加载成功: {js_file_path}")
            return True
        except Exception as e:
            self._logger.error(f"JS文件加载失败: {js_file_path}, 错误: {e}")
            return False

    def execute_function(self, js_file_path: str, function_name: str, *args) -> Any:
        if js_file_path not in self._contexts:
            if not self.load_js_file(js_file_path):
                return None

        context = self._contexts[js_file_path]
        try:
            result = context.call(function_name, *args)
            return result
        except Exception as e:
            self._logger.error(f"JS函数执行失败: {function_name}, 错误: {e}")
            return None

    def generate_params(self, js_file_path: str, params: dict) -> Optional[dict]:
        result = self.execute_function(js_file_path, 'generateParams', params)
        if result and isinstance(result, str):
            import json
            try:
                return json.loads(result)
            except:
                return None
        return result

    def generate_sign(self, js_file_path: str, data: str) -> Optional[str]:
        return self.execute_function(js_file_path, 'generateSign', data)

    def encrypt_data(self, js_file_path: str, data: str) -> Optional[str]:
        return self.execute_function(js_file_path, 'encrypt', data)

    def decrypt_data(self, js_file_path: str, data: str) -> Optional[str]:
        return self.execute_function(js_file_path, 'decrypt', data)

    def clear_context(self, js_file_path: str):
        self._contexts.pop(js_file_path, None)

    def clear_all_contexts(self):
        self._contexts.clear()

    def is_loaded(self, js_file_path: str) -> bool:
        return js_file_path in self._contexts

    def get_loaded_files(self):
        return list(self._contexts.keys())