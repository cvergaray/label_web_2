import elements

from PIL import Image
from elements.ImageElement.Element import element_image_base


class ImageFileElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def element_key():
        return 'image_file'

    @staticmethod
    def can_process(element):
        return element['type'] == ImageFileElement.element_key()

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        try:
            file_path = element.get('file')

            print('loading image from ' + str(file_path))

            image = Image.open(file_path)
            if image is None:
                print("Error reading file!")
            im = element_image_base(image, element, im, margins, dimensions, **kwargs)
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)

        return im

    @staticmethod
    def get_definition():
        return {}
