import elements
import requests


class GrocyApiElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def can_process(element):
        return element['type'] == 'grocy_api'

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        # Base endpoint and API key
        server = element.get('endpoint')
        api_key = element.get('api_key')
        api_path = element.get('api_path', '/')

        # Build full URL (simple join, assume user passes leading slash in api_path)
        if server is None:
            raise ValueError('grocy_api element requires "endpoint"')

        url = f"{server.rstrip('/')}{api_path}"

        # Merge headers with Grocy auth header
        headers = element.get('headers', {})
        if api_key:
            headers = headers | {"GROCY-API-KEY": api_key}
        headers = headers | {"accept": "application/json"}

        # Only GET is supported
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response_data = response.json()

        # Pass response data to child elements, like json_api
        sub_elements = element.get('elements', [])
        for sub_element in sub_elements:
            sub_element_key = sub_element.get('key')
            if isinstance(response_data, dict) and sub_element_key is not None and sub_element_key in response_data:
                sub_element['data'] = response_data[sub_element_key]
            else:
                sub_element['data'] = response_data
            self.process_with_plugins(sub_element, im, margins, dimensions, payload, **kwargs)

        return im
