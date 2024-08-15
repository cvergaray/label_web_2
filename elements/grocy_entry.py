import elements


class GrocyEntryElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def element_key():
        return 'grocy_entry'

    @staticmethod
    def can_process(element):
        return element['type'] == GrocyEntryElement.element_key()

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        server = element.get('endpoint')
        api_key = element.get('api_key')
        grocycode = element.get('grocycode', kwargs.get('grocycode')).split(':')
        grocycode_type = grocycode[1]
        typeid = grocycode[2]
        if grocycode_type == 'p':  # Product
            server = f"{server}/api/stock/products/{typeid}"
            if len(grocycode) > 3:
                server = f"{server}/entries?query%5B%5D=stock_id%3D{grocycode[3]}"
        elif grocycode_type == 'c':  # Chore
            server = f"{server}/api/chores/{typeid}"
        elif grocycode_type == 'b':  # battery
            server = f"{server}/api/battery/{typeid}"

        element['type'] = 'json_api'
        element['endpoint'] = server
        headers = element.get('headers', {})
        element['headers'] = headers | {"GROCY-API-KEY": api_key}

        im = self.process_with_plugins(element, im, margins, dimensions, **kwargs)

        return im

    @staticmethod
    def get_definition():
        return {
            GrocyEntryElement.element_key(): {
                "type": "object",
                "id": GrocyEntryElement.element_key(),
                "defaultProperties": [
                    "type",
                    "endpoint",
                    "api_key",
                    "elements",
                ],
                "requiredProperties": [
                    "type",
                    "endpoint",
                    "api_key"
                ],
                "properties": {
                    "name": {
                        "type": "string",
                    },
                    "type": {
                        "type": "string",
                        "enum": [GrocyEntryElement.element_key()],
                        "options": {
                            "hidden": "true"
                        }
                    },
                    "grocycode": {
                        "type": "string",
                        "title": "Grocy Code",
                        "description": "Hardcoded Grocy Code to be used with the request. If omitted, the " +
                                       "http request for printing the label must include this property.",
                    },
                    "elements": {
                        "type": "array",
                        "title": "Grocy Entry Sub Elements",
                        "items": {
                            "title": "Sub-Element",
                            "anyOf": GrocyEntryElement.get_plugin_editor_keys()
                        }
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
                    },
                    "api_key": {
                        "type": "string",
                        "title": "API Key",
                        "description": "The Grocy API key for the request"
                    }
                }
            }
        }
