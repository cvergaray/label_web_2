import elements
from PIL import Image


class DataMatrixElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def element_key():
        return 'datamatrix'

    @staticmethod
    def can_process(element):
        return element['type'] == DataMatrixElement.element_key()

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

    @staticmethod
    def get_definition():
        return {
            "datamatrix": {
                "type": "object",
                "id": "datamatrix",
                "defaultProperties": [
                    "type",
                    "data",
                    "horizontal_offset",
                    "vertical_offset"
                ],
                "required": [
                    "type",
                    "horizontal_offset",
                    "vertical_offset"
                ],
                "properties": {
                    "name": {
                        "type": "string",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["datamatrix"]
                    },
                    "data": {
                        "type": "string",
                        "description": "Hard-coded text value to be rendered or source for datakey"
                    },
                    "key": {
                        "type": "string",
                        "description": "The key identifying the item from the HTML request that will be rendered."
                    },
                    "datakey": {
                        "type": "string",
                        "description": "The value from with the data property that will be used as data"
                    },
                    "size": {
                        "type": "string",
                        "enum": ["RectAuto", "SquareAuto", "ShapeAuto", "10x10", "12x12", "14x14", "16x16", "18x18",
                                 "20x20", "22x22", "24x24", "26x26", "32x32", "36x36", "40x40", "44x44", "48x48",
                                 "52x52", "64x64", "72x72", "80x80", "88x88", "96x96", "104x104", "120x120", "132x132",
                                 "144x144", "8x18", "8x32", "12x26", "12x36", "16x36", "16x48"],
                        "default": "SquareAuto"
                    },
                    "horizontal_offset": {
                        "title": "Horizontal Offset",
                        "type": 'integer',
                        "minimum": 0,
                    },
                    "vertical_offset": {
                        "title": "Vertical Offset",
                        "type": 'integer',
                        "minimum": 0
                    }
                }
            }
        }
