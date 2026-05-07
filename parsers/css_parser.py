from lxml import html
from lxml.cssselect import CSSSelector
from typing import List, Dict, Any, Optional


class CSSParser:
    @staticmethod
    def parse_list(html_content: str, list_selector: str, fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            tree = html.fromstring(html_content)
            selector = CSSSelector(list_selector)
            items = selector(tree)
        except Exception as e:
            return []

        news_list = []
        for item in items:
            news_item = {}

            for field_name, field_config in fields.items():
                try:
                    if isinstance(field_config, str):
                        sel = CSSSelector(field_config)
                        elements = sel(item)
                        if elements:
                            news_item[field_name] = CSSParser._get_text(elements[0])
                        else:
                            news_item[field_name] = None
                    elif isinstance(field_config, dict):
                        css_selector = field_config.get('selector', '')
                        attr = field_config.get('attr', 'text')

                        sel = CSSSelector(css_selector)
                        elements = sel(item)
                        if elements:
                            element = elements[0]
                            if attr == 'text':
                                news_item[field_name] = CSSParser._get_text(element)
                            elif attr == 'href':
                                news_item[field_name] = CSSParser._get_attribute(element, 'href')
                            elif attr == 'src':
                                news_item[field_name] = CSSParser._get_attribute(element, 'src')
                            else:
                                news_item[field_name] = CSSParser._get_attribute(element, attr)
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
    def _get_text(element) -> str:
        if isinstance(element, str):
            return element.strip()
        elif hasattr(element, 'text_content'):
            return element.text_content().strip()
        elif hasattr(element, 'text'):
            return element.text.strip()
        return ''

    @staticmethod
    def _get_attribute(element, attr: str) -> str:
        if hasattr(element, 'get'):
            return element.get(attr, '').strip()
        return ''

    @staticmethod
    def select(html_content: str, css_selector: str) -> List:
        try:
            tree = html.fromstring(html_content)
            selector = CSSSelector(css_selector)
            return selector(tree)
        except Exception:
            return []

    @staticmethod
    def select_first(html_content: str, css_selector: str) -> Optional[Any]:
        results = CSSParser.select(html_content, css_selector)
        return results[0] if results else None