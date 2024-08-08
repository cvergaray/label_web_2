import elements

import textwrap

from PIL import ImageDraw, ImageFont


class TextElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def can_process(element):
        return element['type'] == 'text'

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        data = element.get('data', kwargs.get(element.get('key')))
        datakey = element.get('datakey')
        if datakey is not None and type(data) is dict and datakey in data:
            data = data[datakey]

        if data is None:
            return im

        data = str(data)

        font_path = self.get_value(element, kwargs, 'font_path')
        font_size = self.get_value(element, kwargs, 'font_size')
        fill_color = self.get_value(element, kwargs, 'fill_color')

        horizontal_offset = element['horizontal_offset']
        vertical_offset = element['vertical_offset']

        textoffset = horizontal_offset, vertical_offset

        draw = ImageDraw.Draw(im)

        wrap = element.get('wrap', None)
        if wrap is not None:
            wrapper = textwrap.TextWrapper(width=wrap)
            data = "\n".join(wrapper.wrap(text=data))

        shrink = element.get('shrink', False)
        if shrink:
            font_size = self.adjust_font_to_fit(draw, font_path, font_size, data, dimensions, 2,
                                                horizontal_offset + margins[2],
                                                vertical_offset + margins[3])

        font = ImageFont.truetype(font_path, font_size)

        draw.text(textoffset, data, fill_color, font=font)

        return im
