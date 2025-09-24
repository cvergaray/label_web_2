import elements

from PIL import Image
from elements.ImageElement.Element import element_image_base
import requests


class ImageUrlElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def can_process(element):
        return element['type'] == 'image_url'

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        try:
            url = element.get('url')
            image = Image.open(requests.get(url, stream=True).raw)
            im = element_image_base(image, element, im, margins, dimensions, **kwargs)
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)

        return im

    def get_form_elements(self, element):
        base = super().get_default_form_elements(element)
        base['type'] = 'url'
        base['description'] = base['description'] or 'URL to image'
        return base