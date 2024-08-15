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
        return {}
