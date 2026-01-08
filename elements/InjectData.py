import elements

class InjectData(elements.ElementBase):
    """
    Element to inject data into the payload dictionary or kwargs.
    Options:
        - data: The value to inject.
        - key: The key in the payload or kwargs to inject into.
        - target: 'payload', 'kwargs', or 'children' (default: 'payload').
        - override: Boolean, whether to override existing data (default: False).
    """
    def __init__(self):
        pass

    @staticmethod
    def can_process(element):
        return element.get('type') == 'inject_data'

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        key = element.get('key')
        value = element.get('data')
        target = element.get('target', 'payload')
        override = element.get('override', False)
        sub_elements = element.get('elements', [])
        if key is not None:
            if target == 'kwargs':
                if override or key not in kwargs:
                    kwargs[key] = value
            elif target == 'payload':
                if override or key not in payload:
                    payload[key] = value
            elif target == 'children':
                # Inject into child element definitions within this element's 'elements' list
                for i, sub_el in enumerate(sub_elements):
                    # Only operate on dict-like child definitions
                    if isinstance(sub_el, dict):
                        if override or key not in sub_el:
                            sub_el[key] = value
                    # Assign back in case the list needs explicit update (dicts are mutable but keep consistency)
                    sub_elements[i] = sub_el
                # Ensure updated list is written back
                element['elements'] = sub_elements
            else:
                print("Inject Data: Unknown target specified:", target)

        # If there are children elements, process them
        for sub_element in sub_elements:
            if isinstance(sub_element, dict):
                self.process_with_plugins(sub_element, im, margins, dimensions, payload, **kwargs)

        return im
