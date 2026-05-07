import json
from typing import Dict, List, Any, Optional


class JsonParser:
    @staticmethod
    def parse_list(data: Dict, list_path: str, fields: Dict[str, str]) -> List[Dict[str, Any]]:
        list_data = data
        for key in list_path.split('.'):
            if isinstance(list_data, dict):
                list_data = list_data.get(key, [])
            else:
                return []

        if not isinstance(list_data, list):
            return []

        news_list = []
        for item in list_data:
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

    @staticmethod
    def extract_field(data: Dict, field_path: str) -> Any:
        value = data
        for key in field_path.split('.'):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

    @staticmethod
    def parse_json(text: str) -> Optional[Dict]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None