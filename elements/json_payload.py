import elements


class JsonPayloadElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def element_key():
        return 'from_json_payload'

    @staticmethod
    def can_process(element):
        return element['type'] == JsonPayloadElement.element_key()

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        sub_elements = element.get('elements', [])
        for sub_element in sub_elements:
            sub_element_key = sub_element.get('key')
            if sub_element_key is not None and sub_element_key in payload:
                sub_element['data'] = payload[sub_element_key]
            else:
                sub_element['data'] = payload
            self.process_with_plugins(sub_element, im, margins, dimensions, payload, **kwargs)

        return im

    @staticmethod
    def get_definition():
        return {
            JsonPayloadElement.element_key(): {
                "type": "object",
                "id": JsonPayloadElement.element_key(),
                "defaultProperties": [
                    "type",
                    "key",
                    "elements"
                ],
                "requiredProperties": [
                    "type",
                    "key",
                    "endpoint"
                ],
                "properties": {
                    "name": {
                        "type": "string",
                    },
                    "type": {
                        "type": "string",
                        "enum": [JsonPayloadElement.element_key()],
                        "options": {
                            "hidden": "true"
                        }
                    },
                    "elements": {
                        "type": "array",
                        "title": "JSON Payload Sub Elements",
                        "items": {
                            "title": "Sub-Element",
                            "anyOf": JsonPayloadElement.get_plugin_editor_keys()
                        }
                    },
                    "key": {
                        "type": "string",
                        "title": "Key",
                        "description": "The key of the element from JSON Payload to be set as the data property of " +
                                       "child elements",
                    }
                }
            }
        }
