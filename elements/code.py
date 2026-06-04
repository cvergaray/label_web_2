import elements
from PIL import Image


class CodeElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def element_key():
        return 'code'

    @staticmethod
    def can_process(element):
        # Generic barcode element, type must be "code"
        return element['type'] == CodeElement.element_key()

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        import treepoem

        data = element.get('data', kwargs.get(element.get('key')))
        data_key = element.get('datakey')
        if data_key is not None and isinstance(data, dict) and data_key in data:
            data = data[data_key]

        if not data:
            return im

        # Which barcode type to generate (treepoem barcode_type)
        code_type = element.get('code_type', 'code39')

        img_size = element.get('img_size', None)

        horizontal_offset = element.get('horizontal_offset', 0)
        vertical_offset = element.get('vertical_offset', 0)

        # Generate barcode via treepoem; let treepoem/BWIPP validate data
        try:
            barcode = treepoem.generate_barcode(
                barcode_type=str(code_type),
                data=str(data)
            )
        except Exception as exc:
            # Fail fast with a clear error so the caller/user sees what's wrong
            raise ValueError(
                f"Failed to generate barcode of type '{code_type}' with data '{data}': {exc}"
            ) from exc

        # Convert to RGB so it matches the main label image mode
        barcode = barcode.convert('RGB')

        # Optional: scale to requested image size (pixels)
        if img_size is not None:
            orig_w, orig_h = barcode.size

            # Preserve aspect ratio to avoid unreadable barcodes
            if isinstance(img_size, str) and 'x' in img_size.lower():
                w_str, h_str = img_size.lower().split('x', 1)
                target_w = int(w_str)
                target_h = int(h_str)

                scale = min(target_w / orig_w, target_h / orig_h)
                new_w = max(1, int(orig_w * scale))
                new_h = max(1, int(orig_h * scale))
            else:
                # Single value: treat as desired width and scale height proportionally
                target_w = int(img_size)
                scale = target_w / orig_w
                new_w = target_w
                new_h = max(1, int(orig_h * scale))

            barcode = barcode.resize(
                (new_w, new_h),
                resample=Image.NEAREST
            )

        im.paste(
            barcode,
            (
                horizontal_offset,
                vertical_offset,
                horizontal_offset + barcode.width,
                vertical_offset + barcode.height
            )
        )

        return im

    def get_form_elements(self, element):
        form = self.get_default_form_elements(element)
        if form is None:
            return None
        form['required'] = True
        form['description'] = form['description'] or element.get('code_type', 'code39') + ' barcode to be generated'
        return [form]

    @staticmethod
    def get_definition():
        return {
            CodeElement.element_key(): {
                "type": "object",
                "id": CodeElement.element_key(),
                "defaultProperties": [
                    "type",
                    "code_type",
                    "data",
                    "horizontal_offset",
                    "vertical_offset"
                ],
                "required": [
                    "type",
                    "code_type",
                    "horizontal_offset",
                    "vertical_offset"
                ],
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "type": {
                        "type": "string",
                        "enum": [CodeElement.element_key()],
                        "options": {
                            "hidden": "true"
                        }
                    },
                    "code_type": {
                        "type": "string",
                        "title": "Barcode Type",
                        "default": "code39",
                        "description": "treepoem/BWIPP barcode type (for example: code39, qrcode, code128)."
                    },
                    "data": {
                        "type": "string",
                        "description": "Hard-coded barcode value to be rendered"
                    },
                    "key": {
                        "type": "string",
                        "description": "Request key used as barcode value."
                    },
                    "datakey": {
                        "type": "string",
                        "description": "Nested key when the resolved data is an object."
                    },
                    "img_size": {
                        "type": ["string", "integer"],
                        "title": "Image Size",
                        "description": "Optional output size in pixels, like 200 or 200x100."
                    },
                    "horizontal_offset": {
                        "title": "Horizontal Offset",
                        "type": "integer",
                        "minimum": 0,
                        "default": 0
                    },
                    "vertical_offset": {
                        "title": "Vertical Offset",
                        "type": "integer",
                        "minimum": 0,
                        "default": 0
                    }
                }
            }
        }

