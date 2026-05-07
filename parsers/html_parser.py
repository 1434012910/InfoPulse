from lxml import html
from typing import List, Dict, Any, Optional


class HtmlParser:
    @staticmethod
    def parse_list(html_content: str, list_selector: str, fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            tree = html.fromstring(html_content)
            items = tree.xpath(list_selector)
        except Exception as e:
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
                    news_item[field_name] = None

            if news_item.get('title'):
                news_list.append(news_item)

        return news_list

    @staticmethod
    def extract_text(element) -> str:
        if hasattr(element, 'text_content'):
            return element.text_content().strip()
        elif hasattr(element, 'text'):
            return element.text.strip()
        return ''

    @staticmethod
    def extract_attribute(element, attr: str) -> str:
        if hasattr(element, 'get'):
            return element.get(attr, '').strip()
        return ''

    @staticmethod
    def parse_html(html_content: str) -> Optional[html.HtmlElement]:
        try:
            return html.fromstring(html_content)
        except Exception:
            return None