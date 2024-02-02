#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is a web service to print labels on Brother QL label printers.
"""

import cups

import textwrap

import sys, logging, random, json, argparse
from io import BytesIO

from bottle import run, route, get, post, response, request, jinja2_view as view, static_file, redirect
from PIL import Image, ImageDraw, ImageFont

from brother_ql.devicedependent import models, label_type_specs, label_sizes
from brother_ql.devicedependent import ENDLESS_LABEL, DIE_CUT_LABEL, ROUND_DIE_CUT_LABEL
from brother_ql import BrotherQLRaster, create_label
from brother_ql.backends import backend_factory, guess_backend

#uncomment the printer-specific implementation you wish to use
#from implementation_brother import implementation
from implementation_cups import implementation

from font_helpers import get_fonts

logger = logging.getLogger(__name__)
instance = implementation()

LABEL_SIZES = instance.get_label_sizes()

try:
    with open('config.json', encoding='utf-8') as fh:
        CONFIG = json.load(fh)
except FileNotFoundError as e:
    with open('config.example.json', encoding='utf-8') as fh:
        CONFIG = json.load(fh)


@route('/')
def index():
    redirect('/labeldesigner')

@route('/static/<filename:path>')
def serve_static(filename):
    return static_file(filename, root='./static')

@route('/labeldesigner')
@view('labeldesigner.jinja2')
def labeldesigner():
    font_family_names = sorted(list(FONTS.keys()))
    return {'font_family_names': font_family_names,
            'fonts': FONTS,
            'label_sizes': LABEL_SIZES,
            'website': CONFIG['WEBSITE'],
            'label': CONFIG['LABEL']}
    
@get('/api/print/template/<templatefile>')
@post('/api/print/template/<templatefile>')
def printtemplate(templatefile):
    return_dict = {'Success': False}
    template_data = get_template_data(templatefile)
        
    try:
        context = get_label_context(request)
    except LookupError as e:
        return_dict['error'] = e.message
        return return_dict
        
    im = create_label_from_template(template_data, **context)
    if DEBUG:
        im.save('sample-out.png')
    
    return instance.print_label(im, **context)
    
def get_template_data(templatefile):
    template_data = None
    with open(templatefile, 'r') as file:
        template_data = json.load(file)
    return template_data

def create_label_from_template(template, **kwargs):
    width, height = instance.get_label_width_height(get_value(template, kwargs, 'font_path'), **kwargs)
    width = template.get('width', width)
    height = template.get('height', height)
    dimensions = width, height
    
    margin_left = get_value(template, kwargs, 'margin_left', 15)
    margin_top = get_value(template, kwargs, 'margin_top', 22)
    margin_right = get_value(template, kwargs, 'margin_right', margin_left)
    margin_bottom = get_value(template, kwargs, 'margin_bottom', margin_top)
    margins = [margin_left, margin_top, margin_right, margin_bottom]
    
    im = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(im)

    elements = template.get('elements', [])
    for element in elements:
        element_type = element['type']
        if element_type == 'datamatrix':
            im = element_datamatrix(element, im, margins, dimensions, **kwargs)
        elif element_type == 'text':
            im = element_text(element, im, margins, dimensions, **kwargs)
    
    return im
    
def get_value(template, kwargs, keyname, default=None):
    return template.get(keyname, kwargs.get(keyname, default))
    
def element_datamatrix(element, im, margins, dimensions, **kwargs):
    from pylibdmtx.pylibdmtx import encode
    data = element.get('data', kwargs.get(element.get('key')))
    size = element.get('size', 'SquareAuto')
    
    horizontal_offset = element['horizontal_offset']
    vertical_offset = element['vertical_offset']
    
    encoded = encode(data.encode('utf8'), size=size) # adjusted for 300x300 dpi - results in DM code roughly 5x5mm
    datamatrix = Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
    datamatrix.save('/tmp/dmtx.png')
    
    im.paste(datamatrix, (horizontal_offset, vertical_offset, horizontal_offset + encoded.width, vertical_offset + encoded.height))

    return im
    
def element_text(element, im, margins, dimensions, **kwargs):
    data = element.get('data', kwargs.get(element.get('key')))
    
    if data is None:
        return im

    font_path = get_value(element, kwargs, 'font_path')
    font_size = get_value(element, kwargs, 'font_size')
    fill_color = get_value(element, kwargs, 'fill_color')
        
    horizontal_offset = element['horizontal_offset']
    vertical_offset = element['vertical_offset']
    
    textoffset = horizontal_offset, vertical_offset
    
    draw = ImageDraw.Draw(im)
    
    wrap = element.get('wrap', None)
    if wrap is not None:
        wrapper = textwrap.TextWrapper(width=wrap)
        data = "\n".join(wrapper.wrap(text = data))
    
    shrink = element.get('shrink', False)
    if shrink:
        font_size = adjust_font_to_fit(draw, font_path, font_size, data, dimensions, 2, horizontal_offset + margins[2], vertical_offset + margins[3])
        
    font = ImageFont.truetype(font_path, font_size)
    
    draw.text(textoffset, data, fill_color, font=font)
    
    return im
    
def get_label_context(request):
    """ might raise LookupError() """

    d = request.params.decode() # UTF-8 decoded form data

    provided_font_family =  d.get('font_family')
    if provided_font_family is not None:
        font_family = provided_font_family.rpartition('(')[0].strip()
        font_style  = provided_font_family.rpartition('(')[2].rstrip(')')
    else:
        default_fonts = CONFIG.get('LABEL')
        font_family = CONFIG['LABEL']['DEFAULT_FONTS']['family']
        font_style = CONFIG['LABEL']['DEFAULT_FONTS']['style']

    context = {
      'text':          d.get('text', None),
      'font_size': int(d.get('font_size', 40)),
      'font_family':   font_family,
      'font_style':    font_style,
      'label_size':    d.get('label_size', implementation.get_default_label_size()),
      'kind':          instance.get_label_kind(d.get('label_size', implementation.get_default_label_size())),
      'margin':    int(d.get('margin', 10)),
      'threshold': int(d.get('threshold', 70)),
      'align':         d.get('align', 'center'),
      'orientation':   d.get('orientation', 'standard'),
      'margin_top':    float(d.get('margin_top',    24))/100.,
      'margin_bottom': float(d.get('margin_bottom', 45))/100.,
      'margin_left':   float(d.get('margin_left',   35))/100.,
      'margin_right':  float(d.get('margin_right',  35))/100.,
      'grocycode': d.get('grocycode', None),
      'product': d.get('product', None),
      'duedate': d.get('due_date', d.get('duedate', None))
    }
    context['margin_top']    = int(context['font_size']*context['margin_top'])
    context['margin_bottom'] = int(context['font_size']*context['margin_bottom'])
    context['margin_left']   = int(context['font_size']*context['margin_left'])
    context['margin_right']  = int(context['font_size']*context['margin_right'])

    context['fill_color']  = (255, 0, 0) if 'red' in context['label_size'] else (0, 0, 0)

    def get_font_path(font_family_name, font_style_name):
        try:
            if font_family_name is None or font_style_name is None or not font_family_name in FONTS or not font_style_name in FONTS[font_family_name]:
                font_family_name = CONFIG['LABEL']['DEFAULT_FONTS']['family']
                font_style_name =  CONFIG['LABEL']['DEFAULT_FONTS']['style']
            font_path = FONTS[font_family_name][font_style_name]
        except KeyError:
            raise LookupError("Couln't find the font & style")
        return font_path

    context['font_path'] = get_font_path(context['font_family'], context['font_style'])

    width, height = instance.get_label_dimensions(context['label_size'])
    #print(width, ' ', height)
    if height > width: width, height = height, width
    if context['orientation'] == 'rotated': height, width = width, height
    context['width'], context['height'] = width, height

    return context

def create_label_im(text, **kwargs):
    im_font = ImageFont.truetype(kwargs['font_path'], kwargs['font_size'])
    im = Image.new('L', (20, 20), 'white')
    draw = ImageDraw.Draw(im)
    # workaround for a bug in multiline_textsize()
    # when there are empty lines in the text:
    lines = []
    for line in text.split('\n'):
        if line == '': line = ' '
        lines.append(line)
    text = '\n'.join(lines)
    linesize = im_font.getsize(text)
    textsize = draw.multiline_textsize(text, font=im_font)
    width, height = instance.get_label_width_height(textsize, **kwargs)
    adjusted_text_size = adjust_font_to_fit(draw, kwargs['font_path'], kwargs['font_size'], text, (width, height), 2, kwargs['margin_left'] + kwargs['margin_right'], kwargs['margin_top'] + kwargs['margin_bottom'])
    if adjusted_text_size != textsize:
        im_font = ImageFont.truetype(kwargs['font_path'], adjusted_text_size)
    im = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(im)
    offset = instance.get_label_offset(width, height, textsize, **kwargs)
    draw.multiline_text(offset, text, kwargs['fill_color'], font=im_font, align=kwargs['align'])
    return im
    
def adjust_font_to_fit(draw, font, max_font_size, text, label_size, min_size = 2, horizontal_offset=0, vertical_offset=0):
    if min_size >= max_font_size or font_fits(draw, font, max_font_size, text, label_size, horizontal_offset, vertical_offset):
        return max_font_size
    high = max_font_size
    low = min_size
    
    while low < high:
        available_range = high - low
        mid = (available_range // 2) + low
        # print('Finding Largest Possible Font between [', low, ',', high, '] with offset of [', horizontal_offset, ',', vertical_offset, '] - Trying: ', mid)
        fits = font_fits(draw, font, mid, text, label_size, horizontal_offset, vertical_offset)
        
        if fits:
            low = mid + 1
        else:
            high = mid
    
    if not font_fits(draw, font, mid, text, label_size, horizontal_offset, vertical_offset):
        mid -= 1
    
    # print('Largest font size: ', mid)
    return mid       
    
def font_fits(draw, font, font_size, text, label_size, horizontal_offset, vertical_offset):
    im_font = ImageFont.truetype(font, font_size)
    textsize = draw.multiline_textsize(text, font=im_font)
    fits = (textsize[0] + horizontal_offset) < label_size[0] and (textsize[1] + vertical_offset) < label_size[1]
    return fits
    
def create_label_grocy(text, **kwargs):
    product = kwargs['product']
    duedate = kwargs['duedate']
    grocycode = kwargs['grocycode']
    margin_left = 15 #kwargs['margin_left']
    margin_top = 22 #kwargs['margin_top']
    margin_right = margin_left #kwargs['margin_right']
    margin_bottom = margin_top #kwargs['margin_bottom']
    
    wrapper = textwrap.TextWrapper(width=25)
    product = "\n".join(wrapper.wrap(text = product))

    # prepare grocycode datamatrix
    from pylibdmtx.pylibdmtx import encode
    encoded = encode(grocycode.encode('utf8'), size="SquareAuto") # adjusted for 300x300 dpi - results in DM code roughly 5x5mm
    datamatrix = Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
    datamatrix.save('/tmp/dmtx.png')

    product_font = ImageFont.truetype(kwargs['font_path'], kwargs['font_size'])
    duedate_font = ImageFont.truetype(kwargs['font_path'], int(kwargs['font_size'] * 0.6))
    
    width, height = instance.get_label_width_height(product_font, **kwargs)

    if kwargs['orientation'] == 'rotated':
        tw = width
        width = height
        height = tw

    im = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(im)
    horizontal_offset = 0
    vertical_offset = 0
    if kwargs['orientation'] == 'standard':
        vertical_offset = margin_top
        horizontal_offset = margin_left
    elif kwargs['orientation'] == 'rotated':
        vertical_offset = margin_top
        horizontal_offset = margin_left
        datamatrix.transpose(Image.ROTATE_270)

    im.paste(datamatrix, (horizontal_offset, vertical_offset, horizontal_offset + encoded.width, vertical_offset + encoded.height))

    if kwargs['orientation'] == 'standard':
        vertical_offset += -10
        horizontal_offset = encoded.width + 40
    elif kwargs['orientation'] == 'rotated':
        vertical_offset += encoded.width + 40
        horizontal_offset += -10

    textoffset = horizontal_offset, vertical_offset
    adjusted_product_font_size = adjust_font_to_fit(draw, kwargs['font_path'], kwargs['font_size'], product, (width, height), 2, horizontal_offset + margin_right, vertical_offset + margin_bottom)
    if kwargs['font_size'] != adjusted_product_font_size:
        product_font = ImageFont.truetype(kwargs['font_path'], adjusted_product_font_size)
    
    draw.text(textoffset, product, kwargs['fill_color'], font=product_font)

    if duedate is not None:
        additional_offset = draw.multiline_textsize(product, font=product_font)[1] + 10

        if kwargs['orientation'] == 'standard':
            vertical_offset += additional_offset
            #horizontal_offset = margin_left
        elif kwargs['orientation'] == 'rotated':
            #vertical_offset = margin_left
            horizontal_offset += additional_offset
        textoffset = horizontal_offset, vertical_offset
        
        adjusted_duedate_font_size = adjust_font_to_fit(draw, kwargs['font_path'], kwargs['font_size'], duedate, (width, height), 2, horizontal_offset + margin_right, vertical_offset + margin_bottom)
        duedate_font = ImageFont.truetype(kwargs['font_path'], adjusted_duedate_font_size)

        draw.text(textoffset, duedate, kwargs['fill_color'], font=duedate_font)

    return im

@get('/api/preview/text')
@post('/api/preview/text')
def get_preview_image():
    context = get_label_context(request)
    im = create_label_im(**context)
    return_format = request.query.get('return_format', 'png')
    if return_format == 'base64':
        import base64
        response.set_header('Content-type', 'text/plain')
        return base64.b64encode(image_to_png_bytes(im))
    else:
        response.set_header('Content-type', 'image/png')
        return image_to_png_bytes(im)


@get('/api/preview/grocy')
@post('/api/preview/grocy')
def get_preview_grocy_image():
    context = get_label_context(request)
    im = create_label_grocy(**context)
    return_format = request.query.get('return_format', 'png')
    if return_format == 'base64':
        import base64
        response.set_header('Content-type', 'text/plain')
        return base64.b64encode(image_to_png_bytes(im))
    else:
        response.set_header('Content-type', 'image/png')
        return image_to_png_bytes(im)
        
@get('/api/preview/template/<templatefile>')
@post('/api/preview/template/<templatefile>')
def get_preview_template_image(templatefile):
    context = get_label_context(request)
    template_data = get_template_data(templatefile)

    im = create_label_from_template(template_data, **context)
    return_format = request.query.get('return_format', 'png')
    if return_format == 'base64':
        import base64
        response.set_header('Content-type', 'text/plain')
        return base64.b64encode(image_to_png_bytes(im))
    else:
        response.set_header('Content-type', 'image/png')
        return image_to_png_bytes(im)


def image_to_png_bytes(im):
    image_buffer = BytesIO()
    im.save(image_buffer, format="PNG")
    image_buffer.seek(0)
    return image_buffer.read()

@post('/api/print/grocy')
@get('/api/print/grocy')
def print_grocy():
    """
    API endpoint to consume the grocy label webhook.

    returns; JSON
    """
    return_dict = {'success' : False }

    try:
        context = get_label_context(request)
    except LookupError as e:
        return_dict['error'] = e.message
        return return_dict

    if context['product'] is None:
        return_dict['error'] = 'Please provide the product for the label'
        return return_dict

    im = create_label_grocy(**context)
    if DEBUG:
        im.save('sample-out.png')
        
    return instance.print_label(im, **context)

@post('/api/print/text')
@get('/api/print/text')
def print_text():
    """
    API to print a label

    returns: JSON

    Ideas for additional URL parameters:
    - alignment
    """

    return_dict = {'success': False}

    try:
        context = get_label_context(request)
    except LookupError as e:
        return_dict['error'] = e.message
        return return_dict

    if context['text'] is None:
        return_dict['error'] = 'Please provide the text for the label'
        return return_dict

    im = create_label_im(**context)
    if DEBUG: im.save('sample-out.png')

    return instance.print_label(im, **context)

def main():
    global DEBUG, FONTS, BACKEND_CLASS, CONFIG
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', default=False)
    parser.add_argument('--loglevel', type=lambda x: getattr(logging, x.upper()), default=False)
    parser.add_argument('--font-folder', default=False, help='folder for additional .ttf/.otf fonts')
    parser.add_argument('--default-label-size', default=False, help='Label size inserted in your printer. Defaults to 62.')
    parser.add_argument('--default-orientation', default=False, choices=('standard', 'rotated'), help='Label orientation, defaults to "standard". To turn your text by 90°, state "rotated".')
    parser.add_argument('--model', default=False, choices=models, help='The model of your printer (default: QL-500)')
    parser.add_argument('printer',  nargs='?', default=False, help='String descriptor for the printer to use (like tcp://192.168.0.23:9100 or file:///dev/usb/lp0)')
    args = parser.parse_args()

    if args.printer:
        CONFIG['PRINTER']['PRINTER'] = args.printer

    if args.port:
        PORT = args.port
    else:
        PORT = CONFIG['SERVER']['PORT']

    if args.loglevel:
        LOGLEVEL = args.loglevel
    else:
        LOGLEVEL = CONFIG['SERVER']['LOGLEVEL']

    if LOGLEVEL == 'DEBUG':
        DEBUG = True
    else:
        DEBUG = False

    instance.DEBUG = DEBUG

    if args.model:
        CONFIG['PRINTER']['MODEL'] = args.model

    if args.default_label_size:
        CONFIG['LABEL']['DEFAULT_SIZE'] = args.default_label_size

    if args.default_orientation:
        CONFIG['LABEL']['DEFAULT_ORIENTATION'] = args.default_orientation

    if args.font_folder:
        ADDITIONAL_FONT_FOLDER = args.font_folder
    else:
        ADDITIONAL_FONT_FOLDER = CONFIG['SERVER']['ADDITIONAL_FONT_FOLDER']


    logging.basicConfig(level=LOGLEVEL)
    instance.logger = logger
    instance.CONFIG = CONFIG

    initialization_errors = instance.initialize()
    if len(initialization_errors) > 0:
        parser.error(initialization_errors)

    if CONFIG['LABEL']['DEFAULT_SIZE'] not in label_sizes:
        parser.error("Invalid --default-label-size. Please choose on of the following:\n:" + " ".join(label_sizes))

    FONTS = get_fonts()
    if ADDITIONAL_FONT_FOLDER:
        FONTS.update(get_fonts(ADDITIONAL_FONT_FOLDER))

    if not FONTS:
        sys.stderr.write("Not a single font was found on your system. Please install some or use the \"--font-folder\" argument.\n")
        sys.exit(2)

    for font in CONFIG['LABEL']['DEFAULT_FONTS']:
        try:
            FONTS[font['family']][font['style']]
            CONFIG['LABEL']['DEFAULT_FONTS'] = font
            logger.debug("Selected the following default font: {}".format(font))
            break
        except: pass
    if CONFIG['LABEL']['DEFAULT_FONTS'] is None:
        sys.stderr.write('Could not find any of the default fonts. Choosing a random one.\n')
        family =  random.choice(list(FONTS.keys()))
        style =   random.choice(list(FONTS[family].keys()))
        CONFIG['LABEL']['DEFAULT_FONTS'] = {'family': family, 'style': style}
        sys.stderr.write('The default font is now set to: {family} ({style})\n'.format(**CONFIG['LABEL']['DEFAULT_FONTS']))

    run(host=CONFIG['SERVER']['HOST'], port=PORT, debug=DEBUG)

if __name__ == "__main__":
    main()
