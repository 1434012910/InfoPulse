from lxml import html
from typing import List, Dict, Any, Optional


class XPathParser:
    @staticmethod
    def parse_list(html_content: str, list_xpath: str, fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            tree = html.fromstring(html_content)
            items = tree.xpath(list_xpath)
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
                            if isinstance(value[0], str):
                                news_item[field_name] = value[0].strip()
                            else:
                                news_item[field_name] = HtmlElementWrapper(value[0]).text()
                        else:
                            news_item[field_name] = None
                    elif isinstance(field_config, dict):
                        xpath = field_config.get('xpath', '')
                        attr = field_config.get('attr', 'text')

                        elements = item.xpath(xpath)
                        if elements:
                            element = elements[0]
                            if attr == 'text':
                                if isinstance(element, str):
                                    value = element.strip()
                                else:
                                    value = HtmlElementWrapper(element).text()
                            elif attr == 'href':
                                value = HtmlElementWrapper(element).get('href', '')
                            elif attr == 'src':
                                value = HtmlElementWrapper(element).get('src', '')
                            else:
                                value = HtmlElementWrapper(element).get(attr, '')

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
    def extract_by_xpath(element, xpath: str) -> List:
        try:
            return element.xpath(xpath)
        except Exception:
            return []

    @staticmethod
    def get_text(element) -> str:
        if isinstance(element, str):
            return element.strip()
        elif hasattr(element, 'text_content'):
            return element.text_content().strip()
        elif hasattr(element, 'text'):
            return element.text.strip()
        return ''

    @staticmethod
    def get_attribute(element, attr: str) -> str:
        if hasattr(element, 'get'):
            return element.get(attr, '').strip()
        return ''


class HtmlElementWrapper:
    def __init__(self, element):
        self.element = element

    def text(self) -> str:
        if isinstance(self.element, str):
            return self.element.strip()
        elif hasattr(self.element, 'text_content'):
            return self.element.text_content().strip()
        elif hasattr(self.element, 'text'):
            return self.element.text.strip()
        return ''

    def get(self, attr: str, default: str = '') -> str:
        if hasattr(self.element, 'get'):
            return self.element.get(attr, default).strip()
        return default