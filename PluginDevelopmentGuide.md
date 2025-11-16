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
