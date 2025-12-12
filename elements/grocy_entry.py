import elements
import requests


class GrocyEntryElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def can_process(element):
        return element['type'] == 'grocy_entry'

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        server = element.get('endpoint')
        api_key = element.get('api_key')
        # Determine the Grocycode value.
        # Priority:
        #   1. Value from kwargs['grocycode'] (passed directly in the request context).
        #   2. Value passed via kwargs using this element's key (same pattern as text/code/datamatrix).
        #   3. Value from the shared payload dict ('grocycode' or key-based).
        #   4. Explicit grocycode on this element.
        #   5. Fallback to element["data"].
        key = element.get('key')
        grocycode_value = None
        grocycode_source = None

        # 1) Direct request/context value
        if 'grocycode' in kwargs and kwargs.get('grocycode') is not None:
            grocycode_value = kwargs.get('grocycode')
            grocycode_source = "kwargs['grocycode']"

        # 2) Element key-based value from kwargs (same pattern as other elements)
        if not grocycode_value and key is not None:
            if key in kwargs:
                grocycode_value = kwargs.get(key)
                grocycode_source = f"kwargs['{key}']"
        # 3) From shared payload dict
        if not grocycode_value and isinstance(payload, dict):
            if 'grocycode' in payload and payload.get('grocycode') is not None:
                grocycode_value = payload.get('grocycode')
                grocycode_source = "payload['grocycode']"
            elif key is not None and key in payload:
                grocycode_value = payload.get(key)
                grocycode_source = f"payload['{key}']"

        # 4) Explicit grocycode field on this element
        if not grocycode_value:
            if element.get('grocycode') is not None:
                grocycode_value = element.get('grocycode')
                grocycode_source = "element['grocycode']"

        # 5) Fallback to element['data']
        if not grocycode_value:
            if element.get('data') is not None:
                grocycode_value = element.get('data')
                grocycode_source = "element['data']"

        if not grocycode_value:
            payload_keys = list(payload.keys()) if isinstance(payload, dict) else None
            print('[GrocyEntry] No grocycode found (key=', key, ', kwargs keys=', list(kwargs.keys()), ', payload keys=', payload_keys, ')')
            return im

        print('[GrocyEntry] Using grocycode from', grocycode_source, 'value =', repr(grocycode_value))
        grocycode = str(grocycode_value).split(':')
        grocycode_type = grocycode[1]
        typeid = grocycode[2]

        # Product-based Grocycode
        if grocycode_type == 'p':  # Product
            product_url = f"{server}/api/stock/products/{typeid}"

            # When a stock entry id is present, merge product + entry data
            if len(grocycode) > 3:
                stock_id = grocycode[3]
                entries_url = f"{product_url}/entries?query%5B%5D=stock_id%3D{stock_id}"

                headers = element.get('headers', {})
                headers = headers | {"GROCY-API-KEY": api_key, "accept": "application/json"}

                # First: product overview
                product_response = requests.get(product_url, headers=headers)
                product_response.raise_for_status()
                product_data = product_response.json()

                # Second: stock entries for this stock_id
                entries_response = requests.get(entries_url, headers=headers)
                entries_response.raise_for_status()
                entries_data = entries_response.json()

                # Ensure we work with a list of entries (JSON API normally returns a list)
                if isinstance(entries_data, dict):
                    entries = [entries_data]
                else:
                    entries = entries_data

                # Enrich each entry with product-level information while keeping the
                # top-level structure (list of entries) for backwards compatibility.
                product_obj = product_data.get('product', product_data)
                for entry in entries:
                    # Attach full product object for templates that want product.name etc.
                    entry.setdefault('product', product_obj)
                    # Convenience copies of some common fields (only if not already set)
                    if 'next_due_date' not in entry and 'next_due_date' in product_data:
                        entry['next_due_date'] = product_data['next_due_date']

                # Emulate json_api behavior: provide the merged data directly
                response_data = entries
                sub_elements = element.get('elements', [])
                for sub_element in sub_elements:
                    sub_element_key = sub_element.get('key')
                    # json_api only does key-based extraction when the response is a dict;
                    # here we always pass the full list (as it would be for the entries endpoint).
                    if isinstance(response_data, dict) and sub_element_key is not None and sub_element_key in response_data:
                        sub_element['data'] = response_data[sub_element_key]
                    else:
                        sub_element['data'] = response_data
                    self.process_with_plugins(sub_element, im, margins, dimensions, payload, **kwargs)

                return im

            # No stock entry id: keep old behavior (product overview)
            server = product_url

        elif grocycode_type == 'c':  # Chore
            server = f"{server}/api/chores/{typeid}"
        elif grocycode_type == 'b':  # battery
            server = f"{server}/api/battery/{typeid}"

        # Fallback / legacy path: delegate to JsonAPIElement like before
        element['type'] = 'json_api'
        element['endpoint'] = server
        headers = element.get('headers', {})
        element['headers'] = headers | {"GROCY-API-KEY": api_key}

        im = self.process_with_plugins(element, im, margins, dimensions, **kwargs)

        return im
