import elements

from PIL import Image
from elements.ImageElement.Element import element_image_base, get_base_definition
import requests


class ImageUrlElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def element_key():
        return 'image_url'

    @staticmethod
    def can_process(element):
        return element['type'] == ImageUrlElement.element_key()

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        try:
            url = element.get('url')
            image = Image.open(requests.get(url, stream=True).raw)
            im = element_image_base(image, element, im, margins, dimensions, **kwargs)
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)

        return im

    @staticmethod
    def get_definition():
        definition = get_base_definition()

        definition['id'] = ImageUrlElement.element_key()
        definition['defaultProperties'].insert(len(definition['defaultProperties'])-1, "url")
        definition['required'].append("url")
        definition['properties']['type']["enum"] = [ImageUrlElement.element_key()]
        definition['properties']['url'] = {
                    "type": "string",
                    "description": "URL of the image to include",
                    "format": "url"
                }

        return {
            ImageUrlElement.element_key(): definition
        }
