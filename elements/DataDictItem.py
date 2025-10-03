import elements


class DataDictItemElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def can_process(element):
        return element['type'] == 'data_dict_item'

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        data = element.get('data')
        key = element.get('key')
        sub_elements = element.get('elements', [])

        if type(data) is dict and key in data:
            for sub_element in sub_elements:
                sub_element['data'] = data[key]
                im = self.process_with_plugins(sub_element, im, margins, dimensions, payload, **kwargs)

        return im

        # Return a flat list of form elements for nested elements within data_dict_item.
