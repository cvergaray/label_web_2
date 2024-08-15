import elements


class BasicElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def element_key():
        return 'basic'

    @staticmethod
    def can_process(element):
        return element['type'] == BasicElement.element_key()

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        # Do Stuff here to add visual elements to the im object

        # Return the im object when you're done
        return im

    @staticmethod
    def get_definition():
        return {
            BasicElement.element_key(): {
                "type": "object",
                "id": BasicElement.element_key(),
                "defaultProperties": [
                    "type"
                ],
                "properties": {
                    "name": {
                        "type": "string",
                    },
                    "type": {
                        "type": "string",
                        "enum": [BasicElement.element_key()]
                    }
                }
            }
        }
