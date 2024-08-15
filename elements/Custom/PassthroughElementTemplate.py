import elements


class PassthroughElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def element_key():
        return 'passthrough'

    @staticmethod
    def can_process(element):
        return element['type'] == PassthroughElement.element_key()

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        # Do some sort of transformation on the elements object

        # Get any Sub-Elements
        sub_elements = element.get('elements', [])

        # Process Sub-Elements
        for sub_element in sub_elements:
            im = self.process_with_plugins(sub_element, im, margins, dimensions, payload, **kwargs)

        # return updated image object
        return im

    @staticmethod
    def get_definition():
        return {
            PassthroughElement.element_key(): {
                "type": "object",
                "id": PassthroughElement.element_key(),
                "defaultProperties": [
                    "type",
                    "elements"
                ],
                "properties": {
                    "name": {
                        "type": "string",
                    },
                    "type": {
                        "type": "string",
                        "enum": [PassthroughElement.element_key()],
                        "options": {
                            "hidden": "true"
                        }
                    },
                    "elements": {
                        "type": "array",
                        "title": "Elements",
                        "items": {
                            "title": "Element",
                            "anyOf": PassthroughElement.get_plugin_editor_keys()
                        }
                    }
                }
            }
        }
