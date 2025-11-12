import elements


class DataArrayIndexElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def can_process(element):
        return element['type'] == 'data_array_index'

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        data = element.get('data')
        index = element.get('index', 0)

        if len(data) > index:
            sub_elements = element.get('elements', [])
            for sub_element in sub_elements:
                sub_element['data'] = data[index]
                im = self.process_with_plugins(sub_element, im, margins, dimensions, payload, **kwargs)

        return im


    def get_form_elements(self, element):
        """
        Return a flat list of form elements for nested elements within data_array_index.
        """
        form_elements = []
        sub_elements = element.get('elements', [])
        for sub_element in sub_elements:
            # Find the appropriate handler for the sub_element type
            for plugin in elements.plugins:
                if plugin.can_process(sub_element):
                    if hasattr(plugin, 'get_form_elements'):
                        form_elements.extend(plugin.get_form_elements(sub_element))
                    break
        return form_elements
