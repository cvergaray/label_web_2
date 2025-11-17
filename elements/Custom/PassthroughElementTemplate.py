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

    def get_form_elements(self, element):
        form_elements = []
        sub_elements = element.get('elements', [])
        for sub_element in sub_elements:
            for plugin in elements.ElementBase.plugins:
                if plugin.can_process(sub_element):
                    if hasattr(plugin, 'get_form_elements'):
                        form_elements.extend(plugin.get_form_elements(sub_element))
                    break
        return form_elements
