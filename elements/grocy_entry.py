import elements


class GrocyEntryElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def element_key():
        return 'grocy_entry'

    @staticmethod
    def can_process(element):
        return element['type'] == GrocyEntryElement.element_key()

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        server = element.get('endpoint')
        api_key = element.get('api_key')
        grocycode = element.get('grocycode', kwargs.get('grocycode')).split(':')
        grocycode_type = grocycode[1]
        typeid = grocycode[2]
        if grocycode_type == 'p':  # Product
            server = f"{server}/api/stock/products/{typeid}"
            if len(grocycode) > 3:
                server = f"{server}/entries?query%5B%5D=stock_id%3D{grocycode[3]}"
        elif grocycode_type == 'c':  # Chore
            server = f"{server}/api/chores/{typeid}"
        elif grocycode_type == 'b':  # battery
            server = f"{server}/api/battery/{typeid}"

        element['type'] = 'json_api'
        element['endpoint'] = server
        headers = element.get('headers', {})
        element['headers'] = headers | {"GROCY-API-KEY": api_key}

        im = self.process_with_plugins(element, im, margins, dimensions, **kwargs)

        return im

    @staticmethod
    def get_definition():
        return {}
