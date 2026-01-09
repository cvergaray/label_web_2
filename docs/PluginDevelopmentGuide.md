# Plugin Development Guide

Label Web can be extended with custom element plugins.

# Plugin Types

While plugins are all implemented the same, they can be categorized into two types:
- Rendering: elements that will add something to the label image before it is sent to the printer.
- Non-Rendering: elements that do not add anything to the label image. Typically, these accept data, manipulate it 
somehow, and then pass it to other elements. But, they can also be used to apply logic, such as apply different templates 
depending on what information is passed to the template print API.

## Methods to Implement
There are two functions that all elements must implement:

### Can Process method
```python
@staticmethod
def can_process(element):
    return element['type'] == 'basic'
```
This method accepts an element definition and returns true if the plugin can process that element definition. The most 
basic implementation simply checks that the element type is a string that the plugin expects. A more advanced 
implementation may also validate that required data is included.

### Process Element method
```python
    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        # Do Stuff here to add visual elements to the im object

        # Return the im object when you're done
        return im
```
This parameters to this method are:
- self: the plugin object
- element: a JSON object with the element definition
- im: a Pillow Image object containing previously rendered elements and into which this element is to be added.
- margins: an array of the margins of the label [left, top, right, bottom]
- 

## Retrieving Data from Elements - Using resolve_data

For consistent data retrieval, all element plugins should use the `resolve_data` method from the `ElementBase` class to retrieve data in a standard and consistent way, unless there is a significant reason why it should not. 
This method provides a unified approach to data resolution with support for three distinct semantics:

### The resolve_data Method

The `resolve_data` method implements a three-step priority system for resolving element data:

```python
def resolve_data(element, kwargs, payload=None, default=None, base_key='data'):
```

**Parameters:**
- `element`: The element definition dictionary
- `kwargs`: The kwargs dictionary (has higher priority than payload)
- `payload`: The payload dictionary (optional, used as fallback)
- `default`: Value to return if data cannot be resolved (default: None)
- `base_key`: The element property to use as the base value (default: 'data')

**Data Resolution Priority:**
1. **Starts with the base key** (default: `data`) - Uses `element.get(base_key)` as the initial value
2. **Applies 'key' if provided** - If a `key` property exists, retrieves the value from `kwargs[key]` (preferred) or `payload[key]` (fallback)
3. **Applies 'datakey' if provided** - If a `datakey` property exists and the resolved data is a dictionary, extracts `data[datakey]`

### Usage Example

Instead of manually checking for `data`, `key`, or `datakey` properties in your plugin:

```python
# OLD WAY - Not recommended
def process_element(self, element, im, margins, dimensions, payload, **kwargs):
    # Manual data retrieval (inconsistent and error-prone)
    if 'key' in element:
        value = kwargs.get(element['key']) or payload.get(element['key'])
    else:
        value = element.get('data')
    # ... rest of processing
```

**Use the resolve_data method instead:**

```python
# NEW WAY - Recommended
def process_element(self, element, im, margins, dimensions, payload, **kwargs):
    # Standard data retrieval with full semantics support
    value = self.resolve_data(element, kwargs, payload)
    # ... rest of processing
```

### Advanced Usage

For custom base keys or nested data extraction:

```python
# Retrieve from a custom property with datakey extraction
value = self.resolve_data(element, kwargs, payload, base_key='custom_field')

# Retrieve with a default value if resolution fails
value = self.resolve_data(element, kwargs, payload, default='fallback_value')

# Combine all features
value = self.resolve_data(element, kwargs, payload, base_key='source', default='N/A')
```

### Benefits of Using resolve_data

- **Consistency**: All elements use the same data retrieval logic
- **Flexibility**: Supports multiple ways of specifying data (direct, from kwargs/payload, from nested dicts)
- **Maintainability**: Changes to data resolution logic apply to all elements automatically
- **Standards Compliance**: Aligns with the common patterns used across the codebase

## Rendering plugin
```python
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
    
```
## Form Field Generation for Plugins

All element plugins that require user input for the web UI must implement a `get_form_elements(self, element)` method. This method should return a **list of dictionaries**, each representing a form field. The structure of each dictionary should match the following keys:
- `name`: The field name (string)
- `label`: The label to display in the UI (string)
- `type`: The input type (e.g., 'text', 'number', 'url', etc.)
- `required`: Boolean indicating if the field is required
- `element_type`: The type of the element (string)
- `description`: Help text for the field (string)
- `placeholder`: Placeholder text for the field (string)

If your element has sub-elements (e.g., container or passthrough types), your `get_form_elements` should aggregate the form fields from all children and return a flat list.

**Example:**
```python
    def get_form_elements(self, element):
        form = self.get_default_form_elements(element)
        if form is None:
            return []
        return [form]
```

**Consistency:**
All built-in and custom elements now return a list of form field dicts, even if only one field is present. This ensures the UI and payload generation are consistent for preview and print.
