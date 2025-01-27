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
