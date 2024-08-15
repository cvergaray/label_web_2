import elements

import json
import requests


class JsonAPIElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def element_key():
        return 'json_api'

    @staticmethod
    def can_process(element):
        return element['type'] == JsonAPIElement.element_key()

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):

        endpoint = element.get('endpoint')
        if endpoint is None:
            return im

        method = element.get('method')

        if method is None or method not in ['get', 'post', 'put', 'delete']:
            method = 'get'

        headers = element.get('headers')
        headers = headers | {'accept': 'application/json'}

        data = element.get('data', {})
        datakey = kwargs.get(element.get('datakey'))
        datakeyname = kwargs.get(element.get('datakeyname'), element.get('datakey'))
        if datakey is not None and datakeyname is not None:
            data[datakeyname] = datakey

        if len(data) == 0:
            data = None
        else:
            data = json.dumps(data)

        if method == 'post':
            response_api = requests.post(endpoint, data=data, headers=headers)
        elif method == 'put':
            response_api = requests.put(endpoint, data=data, headers=headers)
        elif method == 'delete':
            response_api = requests.delete(endpoint, data=data, headers=headers)
        else:
            response_api = requests.get(endpoint, data=data, headers=headers)

        response_data = response_api.json()

        sub_elements = element.get('elements', [])
        for sub_element in sub_elements:
            sub_element_key = sub_element.get('key')
            if sub_element_key is not None and sub_element_key in response_data:
                sub_element['data'] = response_data[sub_element_key]
            else:
                sub_element['data'] = response_data
            self.process_with_plugins(sub_element, im, margins, dimensions, payload, **kwargs)

        return

    @staticmethod
    def get_definition():
        return {
            JsonAPIElement.element_key(): {
                "type": "object",
                "id": JsonAPIElement.element_key(),
                "defaultProperties": [
                    "type",
                    "endpoint",
                    "datakey",
                    "elements"
                ],
                "requiredProperties": [
                    "type",
                    "endpoint"
                ],
                "properties": {
                    "name": {
                        "type": "string",
                    },
                    "type": {
                        "type": "string",
                        "enum": [JsonAPIElement.element_key()],
                        "options": {
                            "hidden": "true"
                        }
                    },
                    "elements": {
                        "type": "array",
                        "title": "JSON API Sub Elements",
                        "items": {
                            "title": "Sub-Element",
                            "anyOf": JsonAPIElement.get_plugin_editor_keys()
                        }
                    },
                    "data": {
                        "type": "string",
                        "title": "Data",
                        "description": "Data dictionary, or leave blank if inheriting from parent element.",
                    },
                    "datakey": {
                        "type": "string",
                        "title": "Data Key",
                        "description": "The key of the element from data dictionary to be set as the data property of "
                                       "child elements",
                    },
                    "datakeyname": {
                        "type": "string",
                        "title": "Data Key Name",
                        "description": "The key for the data retrieved with the Data Key when sent with the request"
                    },
                    "headers": {
                        "type": "object",
                        "title": "Headers",
                        "additionalProperties": {
                            "type": ["string"],
                            "items": ["string"]
                        }
                    },
                    "method": {
                        "type": "string",
                        "title": "Method",
                        "enum": ["get", "post", "put", "delete"],
                        "default": "get"
                    },
                    "endpoint": {
                        "type": "string",
                        "title": "Endpoint",
                        "description": "The endpoint of the request"
                    }
                }
            }
        }
