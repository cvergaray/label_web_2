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

        # If this element has a key, also expose the resolved data into the shared
        # payload dict so that other elements with the same key can reuse it
        # (e.g. grocy_entry). This works because payload is passed unchanged
        # through create_label_from_template.
        key = element.get('key')
        if key is not None and data is not None and isinstance(payload, dict) and key not in payload:
            payload[key] = data

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
