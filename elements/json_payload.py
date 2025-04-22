import elements


class JsonPayloadElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def can_process(element):
        return element['type'] == 'from_json_payload'

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        sub_elements = element.get('elements', [])
        for sub_element in sub_elements:
            sub_element_key = sub_element.get('key')
            if sub_element_key is not None and payload is not None and sub_element_key in payload:
                sub_element['data'] = payload[sub_element_key]
            else:
                sub_element['data'] = payload
            self.process_with_plugins(sub_element, im, margins, dimensions, payload, **kwargs)

        return im
