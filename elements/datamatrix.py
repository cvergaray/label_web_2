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
        if data_key is not None and isinstance(data, dict) and data_key in data:
            data = data[data_key]

        if not data:
            return im

        # BACKWARD COMPATIBILITY:
        # "size" is still the libdmtx symbol size as before (e.g. "SquareAuto", "10x10", ...)
        dm_size = element.get('size', 'SquareAuto')

        # NEW:
        # "img_size" is the desired pixel size of the final image (e.g. "120x120" or 120)
        img_size = element.get('img_size', None)

        horizontal_offset = element.get('horizontal_offset', 0)
        vertical_offset = element.get('vertical_offset', 0)

        # Generate DataMatrix with the configured symbol size
        encoded = encode(data.encode('utf8'), size=dm_size)

        datamatrix = Image.frombytes(
            'RGB',
            (encoded.width, encoded.height),
            encoded.pixels
        )

        # --- Optional: scale to requested image size (pixels) -----------------
        if img_size is not None:
            # Allow "120x120", "150x100" or just 120
            if isinstance(img_size, str) and 'x' in img_size.lower():
                w_str, h_str = img_size.lower().split('x', 1)
                target_w = int(w_str)
                target_h = int(h_str)
            else:
                # Single value: make it square
                target_w = target_h = int(img_size)

            # NEAREST keeps the modules sharp
            datamatrix = datamatrix.resize(
                (target_w, target_h),
                resample=Image.NEAREST
            )
        # ----------------------------------------------------------------------

        datamatrix.save('/tmp/dmtx.png')

        im.paste(
            datamatrix,
            (
                horizontal_offset,
                vertical_offset,
                horizontal_offset + datamatrix.width,
                vertical_offset + datamatrix.height
            )
        )

        return im

    def get_form_elements(self, element):
        form = self.get_default_form_elements(element)
        if form is None:
            return None
        form['required'] = True
        form['description'] = form['description'] or 'DataMatrix code to be generated'
        return [form]

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
