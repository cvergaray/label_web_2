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

        # Be defensive: if data is None, do nothing
        if data is None:
            return im

        if len(data) > index:
            sub_elements = element.get('elements', [])
            for sub_element in sub_elements:
                sub_element['data'] = data[index]
                # process_with_plugins mutates im in-place and does not return it,
                # so we MUST NOT assign its return value to im.
                self.process_with_plugins(sub_element, im, margins, dimensions, payload, **kwargs)

        return im


    def get_form_elements(self, element):
        """
        TODO: Add form elements for data array by index
        """
        form_elements = []
        return form_elements