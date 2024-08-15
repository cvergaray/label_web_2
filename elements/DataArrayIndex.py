import elements


class DataArrayIndexElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def element_key():
        return 'data_array_index'

    @staticmethod
    def can_process(element):
        return element['type'] == DataArrayIndexElement.element_key()

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        data = element.get('data')
        index = element.get('index', 0)

        if len(data) > index:
            sub_elements = element.get('elements', [])
            for sub_element in sub_elements:
                sub_element['data'] = data[index]
                im = self.process_with_plugins(sub_element, im, margins, dimensions, payload, **kwargs)

        return im

    @staticmethod
    def get_definition():
        return {
            DataArrayIndexElement.element_key(): {
                "type": "object",
                "id": DataArrayIndexElement.element_key(),
                "defaultProperties": [
                    "type",
                    "index",
                    "elements"
                ],
                "requiredProperties": [
                    "type",
                    "index"
                ],
                "properties": {
                    "name": {
                        "type": "string",
                    },
                    "type": {
                        "type": "string",
                        "enum": [DataArrayIndexElement.element_key()],
                        "options": {
                            "hidden": "true"
                        }
                    },
                    "elements": {
                        "type": "array",
                        "title": "Elements",
                        "items": {
                            "title": "Element",
                            "anyOf": DataArrayIndexElement.get_plugin_editor_keys()
                        }
                    },
                    "data": {
                        "type": "string",
                        "title": "Data",
                        "description": "Data array, or leave blank if inheriting from parent element.",
                    },
                    "index": {
                        "type": "integer",
                        "title": "Index",
                        "default": 0,
                        "description": "The index of the element from data to be set as the data property of child "
                                       "elements",
                    }
                }
            }
        }
