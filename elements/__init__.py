
import os
import traceback
from importlib import util

from PIL import Image, ImageFont


class ElementBase:
    """Basic resource class. Concrete resources will inherit from this one
    """
    plugins = []

    # For every class that inherits from the current,
    # the class name will be added to plugins
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.plugins.append(cls)

    @staticmethod
    def process_with_plugins(element, im: Image, margins, dimensions, payload, **kwargs):
        element_type = element['type']
        # print('Attempting to process element with type {}'.format(element_type))
        for handler in ElementBase.plugins:
            if handler.can_process(element):
                instance = handler()
                # print('Processing element with handler {}'.format(type(instance).__name__))
                instance.process_element(element, im, margins, dimensions, payload, **kwargs)


    @staticmethod
    def get_plugin_editor_definitions():
        definitions = {}
        for handler in ElementBase.plugins:
            instance = handler()
            definitions = definitions | instance.get_definition()
        return definitions

    @staticmethod
    def get_plugin_editor_keys():
        keys = [{
            "title": "none",
            "type": "null"
        }]
        for handler in ElementBase.plugins:
            instance = handler()
            key = instance.element_key()
            keys.append({
                "title": key,
                "$ref": "#/definitions/" + key
            })
        return keys

    @staticmethod
    def get_value(template, kwargs, keyname, default=None):
        return template.get(keyname, kwargs.get(keyname, default))

    @staticmethod
    def adjust_font_to_fit(draw, font, max_font_size, text, label_size, min_size=2, horizontal_offset=0,
                           vertical_offset=0):
        if min_size >= max_font_size or ElementBase.font_fits(draw, font, max_font_size, text, label_size, horizontal_offset,
                                                  vertical_offset):
            return max_font_size
        high = max_font_size
        low = min_size

        while low < high:
            available_range = high - low
            mid = (available_range // 2) + low
            # print('Finding Largest Possible Font between [', low, ',', high, '] with offset of [', horizontal_offset, ',', vertical_offset, '] - Trying: ', mid)
            fits = ElementBase.font_fits(draw, font, mid, text, label_size, horizontal_offset, vertical_offset)

            if fits:
                low = mid + 1
            else:
                high = mid

        if not ElementBase.font_fits(draw, font, mid, text, label_size, horizontal_offset, vertical_offset):
            mid -= 1

        # print('Largest font size: ', mid)
        return mid

    @staticmethod
    def font_fits(draw, font, font_size, text, label_size, horizontal_offset, vertical_offset):
        im_font = ImageFont.truetype(font, font_size)
        textsize = draw.multiline_textbbox((0, 0), text, font=im_font)
        textsize = (textsize[2], textsize[3])
        fits = (textsize[0] + horizontal_offset) < label_size[0] and (textsize[1] + vertical_offset) < label_size[1]
        return fits


# Small utility to automatically load modules
def load_module(load_from_path):
    name = os.path.split(load_from_path)[-1]
    spec = util.spec_from_file_location(name, load_from_path)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def load_modules_from_path(load_from_dir):
    for fileName in os.listdir(load_from_dir):
        # Load only "real modules"
        if not fileName.startswith('.') and \
                not fileName.startswith('__') and fileName.endswith('.py'):
            try:
                load_module(os.path.join(load_from_dir, fileName))
                print("loaded element handler: " + fileName + " successfully")
            except Exception:
                traceback.print_exc()

# Get current path
path = os.path.abspath(__file__)
directoryPath = os.path.dirname(path)

load_modules_from_path(directoryPath)
load_modules_from_path(os.path.join(directoryPath, 'Custom'))