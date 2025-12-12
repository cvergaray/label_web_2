import elements


class GrocyEntryElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def can_process(element):
        return element['type'] == 'grocy_entry'

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        server = element.get('endpoint')
        api_key = element.get('api_key')
        raw_grocycode = element.get('grocycode', payload.get('grocycode', kwargs.get('grocycode')))
        if raw_grocycode is None:
            print('No grocycode found!')
            return im
        grocycode = raw_grocycode.split(':')
        if len(grocycode) < 3:
            print("Invalid grocycode format! Expected format: 'grcy:TYPE:ID[:STOCK_ID]', got '{}'".format(raw_grocycode))
            return im
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

        im = self.process_with_plugins(element, im, margins, dimensions, payload, **kwargs)

        return im
