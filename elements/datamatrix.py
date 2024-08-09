import elements
from PIL import Image


class DataMatrixElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def can_process(element):
        return element['type'] == 'datamatrix'

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        from pylibdmtx.pylibdmtx import encode
        data = element.get('data', kwargs.get(element.get('key')))
        data_key = element.get('datakey')
        if data_key is not None and type(data) is dict and data_key in data:
            data = data[data_key]

        size = element.get('size', 'SquareAuto')

        horizontal_offset = element['horizontal_offset']
        vertical_offset = element['vertical_offset']

        encoded = encode(data.encode('utf8'), size=size)  # adjusted for 300x300 dpi - results in DM code roughly 5x5mm
        datamatrix = Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
        datamatrix.save('/tmp/dmtx.png')

        im.paste(datamatrix,
                 (horizontal_offset, vertical_offset, horizontal_offset + encoded.width,
                  vertical_offset + encoded.height))

        return im
