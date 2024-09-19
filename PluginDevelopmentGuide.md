# Plugin Development Guide

Label Web can be extended with custom element plugins.

# Plugin Types

While plugins are all implemented the same, they can be categorized into two types:
- Rendering: elements that will add something to the label image before it is sent to the printer.
- Non-Rendering: elements that do not add anything to the label image. Typically, these accept data, manipulate it 
somehow, and then pass it to other elements. But, they can also be used to apply logic, such as apply different templates 
depending on what information is passed to the template print API.

