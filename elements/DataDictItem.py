import elements


class DataDictItemElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def element_key():
        return 'data_dict_item'

    @staticmethod
    def can_process(element):
        return element['type'] == DataDictItemElement.element_key()

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        data = element.get('data')
        key = element.get('key')
        seb_elements = element.get('elements', [])

        if type(data) is dict and key in data:
            for sub_element in seb_elements:
                sub_element['data'] = data[key]
                im = self.process_with_plugins(sub_element, im, margins, dimensions, payload, **kwargs)

        return im

    @staticmethod
    def get_definition():
        return {
            DataDictItemElement.element_key(): {
                "type": "object",
                "id": DataDictItemElement.element_key(),
                "defaultProperties": [
                    "type",
                    "index",
                    "elements"
                ],
                "requiredProperties": [
                    "type",
                    "key"
                ],
                "properties": {
                    "name": {
                        "type": "string",
                    },
                    "type": {
                        "type": "string",
                        "enum": [DataDictItemElement.element_key()],
                        "options": {
                            "hidden": "true"
                        }
                    },
                    "elements": {
                        "type": "array",
                        "title": "Elements",
                        "items": {
                            "title": "Element",
                            "anyOf": DataDictItemElement.get_plugin_editor_keys()
                        }
                    },
                    "data": {
                        "type": "string",
                        "title": "Data",
                        "description": "Data dictionary, or leave blank if inheriting from parent element.",
                    },
                    "key": {
                        "type": "string",
                        "title": "Key",
                        "description": "The key of the element from data dictionary to be set as the data property of "
                                       "child elements",
                    }
                }
            }
        }
