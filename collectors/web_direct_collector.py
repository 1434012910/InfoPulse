import requests
from lxml import html
from typing import Dict, List, Any
from .base_collector import BaseCollector


class WebDirectCollector(BaseCollector):
    def _fetch_data(self) -> Any:
        url = self.source_config.get('url')
        headers = self.source_config.get('headers', {})
        cookies = self.source_config.get('cookies', {})
        params = self.source_config.get('params', {})
        timeout = self.source_config.get('timeout', 30)

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
            params=params,
            proxies=proxies,
            timeout=timeout
        )
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')
        if 'json' in content_type:
            return response.json()
        else:
            return response.text

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
        if isinstance(response, dict):
            return self._parse_json_response(response)
        elif isinstance(response, str):
            return self._parse_html_response(response)
        else:
            return []

    def _parse_json_response(self, response: Dict) -> List[Dict[str, Any]]:
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

    def _parse_html_response(self, response: str) -> List[Dict[str, Any]]:
        parse_config = self.source_config.get('parse_config', {})
        list_selector = parse_config.get('list_selector', '')
        fields = parse_config.get('fields', {})

        if not list_selector:
            return []

        try:
            tree = html.fromstring(response)
            items = tree.xpath(list_selector)
        except Exception as e:
            self.logger.error(f"XPath解析失败: {e}")
            return []

        news_list = []
        for item in items:
            news_item = {}

            for field_name, field_config in fields.items():
                try:
                    if isinstance(field_config, str):
                        value = item.xpath(field_config)
                        if value:
                            news_item[field_name] = value[0].strip()
                        else:
                            news_item[field_name] = None
                    elif isinstance(field_config, dict):
                        selector = field_config.get('selector', '')
                        attr = field_config.get('attr', 'text')

                        elements = item.xpath(selector)
                        if elements:
                            element = elements[0]
                            if attr == 'text':
                                value = element.text_content().strip() if hasattr(element, 'text_content') else element.text.strip()
                            elif attr == 'href':
                                value = element.get('href', '').strip()
                            elif attr == 'src':
                                value = element.get('src', '').strip()
                            else:
                                value = element.get(attr, '').strip()

                            news_item[field_name] = value
                        else:
                            news_item[field_name] = None
                    else:
                        news_item[field_name] = None
                except Exception as e:
                    self.logger.warning(f"字段 {field_name} 解析失败: {e}")
                    news_item[field_name] = None

            if news_item.get('title'):
                if news_item.get('url') and not news_item['url'].startswith('http'):
                    base_url = self.source_config.get('url', '')
                    if base_url:
                        from urllib.parse import urljoin
                        news_item['url'] = urljoin(base_url, news_item['url'])

                news_list.append(news_item)

        return news_list