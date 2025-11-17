import elements


class BasicElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def can_process(element):
        return element['type'] == 'basic'

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        # Do Stuff here to add visual elements to the im object

        # Return the im object when you're done
        return im

    def get_form_elements(self, element):
        form = self.get_default_form_elements(element)
        if form is None:
            return []
        return [form]
