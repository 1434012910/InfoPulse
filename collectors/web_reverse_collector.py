import json
import os
import execjs
import requests
from typing import Dict, List, Any
from .base_collector import BaseCollector
from core.logger import Logger


class WebReverseCollector(BaseCollector):
    def __init__(self, source_config: Dict[str, Any], config):
        super().__init__(source_config, config)
        self.js_context = None
        self._load_js_file()

    def _load_js_file(self):
        js_file = self.source_config.get('js_file')
        if not js_file:
            raise ValueError(f"Web逆向采集器必须配置js_file")

        js_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), js_file)
        if not os.path.exists(js_path):
            raise FileNotFoundError(f"JS逆向文件不存在: {js_path}")

        try:
            with open(js_path, 'r', encoding='utf-8') as f:
                js_code = f.read()
            self.js_context = execjs.compile(js_code)
        except Exception as e:
            Logger.log_reverse_alert(self.logger, self.source_name, js_file, str(e))
            raise

    def _fetch_data(self) -> Any:
        url = self.source_config.get('url')
        headers = self.source_config.get('headers', {})
        cookies = self.source_config.get('cookies', {})
        params = self.source_config.get('params', {})
        timeout = self.source_config.get('timeout', 30)

        try:
            sign_params = self.js_context.call('generateParams', params)
            if isinstance(sign_params, str):
                sign_params = json.loads(sign_params)
        except Exception as e:
            Logger.log_reverse_alert(self.logger, self.source_name, 
                                   self.source_config.get('js_file', ''), str(e))
            raise

        proxy_config = self.source_config.get('proxy', {})
        proxies = None
        if proxy_config.get('enabled'):
            proxy_url = self._get_proxy()
            if proxy_url:
                proxies = {'http': proxy_url, 'https': proxy_url}

        session = requests.Session()
        session.headers.update(headers)
        session.cookies.update(cookies)

        response = session.get(
            url,
            params=sign_params,
            proxies=proxies,
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()

    def _get_proxy(self) -> str:
        proxy_config = self.config.get('crawler', {}).get('proxy', {})
        if proxy_config.get('proxy_pool_url'):
            try:
                response = requests.get(proxy_config['proxy_pool_url'], timeout=5)
                return response.text.strip()
            except:
                pass

        proxy_list = proxy_config.get('proxy_list', [])
        if proxy_list:
            import random
            return random.choice(proxy_list)

        return None

    def _parse_response(self, response: Any) -> List[Dict[str, Any]]:
        parse_config = self.source_config.get('parse_config', {})
        list_path = parse_config.get('list_path', 'data')
        fields = parse_config.get('fields', {})

        data = response
        for key in list_path.split('.'):
            if isinstance(data, dict):
                data = data.get(key, [])
            else:
                break

        if not isinstance(data, list):
            return []

        news_list = []
        for item in data:
            if not isinstance(item, dict):
                continue

            news_item = {}
            for field_name, field_path in fields.items():
                if isinstance(field_path, str):
                    value = item
                    for key in field_path.split('.'):
                        if isinstance(value, dict):
                            value = value.get(key)
                        else:
                            value = None
                            break
                    news_item[field_name] = value
                else:
                    news_item[field_name] = field_path

            if news_item.get('title') and news_item.get('url'):
                news_list.append(news_item)

        return news_list