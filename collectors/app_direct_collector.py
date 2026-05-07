import requests
from typing import Dict, List, Any
from .base_collector import BaseCollector


class AppDirectCollector(BaseCollector):
    def _fetch_data(self) -> Any:
        url = self.source_config.get('url')
        headers = self.source_config.get('headers', {})
        params = self.source_config.get('params', {})
        timeout = self.source_config.get('timeout', 30)

        proxy_config = self.source_config.get('proxy', {})
        proxies = None
        if proxy_config.get('enabled'):
            proxy_url = self._get_proxy()
            if proxy_url:
                proxies = {'http': proxy_url, 'https': proxy_url}

        response = requests.get(
            url,
            params=params,
            headers=headers,
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