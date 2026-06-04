import elements

class InjectData(elements.ElementBase):
    """
    Element to inject data into the payload dictionary, kwargs, or child element definitions.

    The data to inject is resolved using the resolve_data method with the following priority:
    1) Uses element.get('data') as the base value.
    2) If 'key' is provided, it tries to resolve the value from kwargs[key] or payload[key].
    3) If 'datakey' is provided and the resolved data is a dict, returns data[datakey].

    Options:
        - data: The value to inject (used as base for resolve_data).
        - key: Optional. If provided, retrieves the value from kwargs or payload using this key.
        - datakey: Optional. If provided and data is a dict, retrieves the value at data[datakey].
        - target_key: The key in the target (payload, kwargs, or child element) to inject into.
        - target: 'payload', 'kwargs', or 'children' (default: 'payload').
        - override: Boolean, whether to override existing data (default: False).
    """
    def __init__(self):
        pass

    @staticmethod
    def element_key():
        return 'inject_data'

    @staticmethod
    def can_process(element):
        return element.get('type') == InjectData.element_key()

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        target_key = element.get('target_key')
        # Use resolve_data to retrieve the value with data/key/datakey semantics
        value = self.resolve_data(element, kwargs, payload)
        target = element.get('target', 'payload')
        override = element.get('override', False)
        sub_elements = element.get('elements', [])
        if target_key is not None:
            if target == 'kwargs':
                if override or target_key not in kwargs:
                    kwargs[target_key] = value
            elif target == 'payload':
                if override or target_key not in payload:
                    payload[target_key] = value
            elif target == 'children':
                # Inject into child element definitions within this element's 'elements' list
                for i, sub_el in enumerate(sub_elements):
                    # Only operate on dict-like child definitions
                    if isinstance(sub_el, dict):
                        if override or target_key not in sub_el:
                            sub_el[target_key] = value
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

    @staticmethod
    def get_definition():
        return {
            InjectData.element_key(): {
                "type": "object",
                "id": InjectData.element_key(),
                "defaultProperties": [
                    "type",
                    "target",
                    "target_key",
                    "override",
                    "elements"
                ],
                "required": [
                    "type",
                    "target",
                    "target_key"
                ],
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "type": {
                        "type": "string",
                        "enum": [InjectData.element_key()],
                        "options": {
                            "hidden": "true"
                        }
                    },
                    "data": {
                        "type": ["string", "number", "boolean", "object", "array", "null"],
                        "title": "Data",
                        "description": "Base data to inject; can be overridden by key lookup."
                    },
                    "key": {
                        "type": "string",
                        "title": "Source Key",
                        "description": "Lookup key used against kwargs or payload before injection."
                    },
                    "datakey": {
                        "type": "string",
                        "title": "Nested Source Key",
                        "description": "If source resolves to an object, pick this nested key."
                    },
                    "target": {
                        "type": "string",
                        "title": "Target",
                        "enum": ["payload", "kwargs", "children"],
                        "default": "payload"
                    },
                    "target_key": {
                        "type": "string",
                        "title": "Target Key",
                        "description": "Name of the key to inject into the selected target."
                    },
                    "override": {
                        "type": "boolean",
                        "title": "Override Existing Value",
                        "default": False
                    },
                    "elements": {
                        "type": "array",
                        "title": "Child Elements",
                        "items": {
                            "title": "Element",
                            "oneOf": InjectData.get_plugin_editor_keys()
                        }
                    }
                }
            }
        }

