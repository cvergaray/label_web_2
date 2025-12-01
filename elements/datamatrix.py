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
        if data_key is not None and isinstance(data, dict) and data_key in data:
            data = data[data_key]

        if not data:
            return im

        # This is the libdmtx *symbol* size ("SquareAuto", "10x10", "12x12", ...)
        dm_size = element.get('dm_size', 'SquareAuto')

        # This is the desired *pixel* size of the final image, e.g. "120x120" or 120
        target_size = element.get('size', None)

        horizontal_offset = element['horizontal_offset']
        vertical_offset = element['vertical_offset']

        # Generate DataMatrix with automatic symbol size
        encoded = encode(data.encode('utf8'), size=dm_size)

        datamatrix = Image.frombytes(
            'RGB',
            (encoded.width, encoded.height),
            encoded.pixels
        )

        # --- Scale the DataMatrix image to a fixed pixel size -----------------
        if target_size is not None:
            # allow "120x120", "150x100" or just 120
            if isinstance(target_size, str) and 'x' in target_size.lower():
                w_str, h_str = target_size.lower().split('x', 1)
                target_w = int(w_str)
                target_h = int(h_str)
            else:
                # single value: make it square
                target_w = target_h = int(target_size)

            # NEAREST keeps the blocks sharp (no blur between black & white)
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
