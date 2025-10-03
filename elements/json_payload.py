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

    def get_form_elements(self, element):
        """
        Return a flat list of form elements for nested elements within json_payload.
        These fields will be marked for JSON payload submission.
        """
        sub_elements = element.get('elements', [])
        result_fields = []

        for sub_element in sub_elements:
            # Get form elements for each nested element
            form_element = self.get_form_elements_with_plugins(sub_element)

            if form_element is not None:
                # Mark each field as part of JSON payload and add to result
                for field in form_element:
                    if isinstance(field, dict):
                        field['json_payload'] = True
                    result_fields.append(field)

        return result_fields

        return None
