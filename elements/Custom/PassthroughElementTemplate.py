import elements


class PassthroughElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def can_process(element):
        return element['type'] == 'passthrough'

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        # Do some sort of transformation on the elements object

        # Get any Sub-Elements
        sub_elements = element.get('elements', [])

        # Process Sub-Elements
        for sub_element in sub_elements:
            im = self.process_with_plugins(sub_element, im, margins, dimensions, payload, **kwargs)

        # return updated image object
        return im