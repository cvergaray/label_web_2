#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is a web service to print labels on label printers via CUPS.
"""
import cups

import textwrap

import sys, logging, random, json, argparse, requests, yaml
from io import BytesIO

from bottle import run, route, get, post, response, request, jinja2_view as view, static_file, redirect
from PIL import Image, ImageDraw, ImageFont

import glob
import os

from elements import ElementBase

from implementation_cups import implementation

from font_helpers import get_fonts

logger = logging.getLogger(__name__)
instance = implementation()

try:
    with open('/appconfig/config.json', encoding='utf-8') as fh:
        CONFIG = json.load(fh)
        print("loaded config from /appconfig/config.json")
except FileNotFoundError as e:
    with open('config.example.json', encoding='utf-8') as fh:
        CONFIG = json.load(fh)
        print("loaded config from config.example.json")

PRINTERS = None
LABEL_SIZES = None


# the decorator
def enable_cors(fn):
    def _enable_cors(*args, **kwargs):
        # set CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

        if request.method != 'OPTIONS':
            # actual request; reply with the actual response
            return fn(*args, **kwargs)

    return _enable_cors


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
    default_printer = instance.selected_printer if instance.selected_printer else (PRINTERS[0] if PRINTERS else None)
    default_orientation = CONFIG['LABEL'].get('DEFAULT_ORIENTATION', 'standard')
    return {'font_family_names': font_family_names,
            'fonts': FONTS,
            'label_sizes': LABEL_SIZES,
            'printers': PRINTERS,
            'default_printer': default_printer,
            'default_orientation': default_orientation,
            'website': CONFIG['WEBSITE'],
            'label': CONFIG['LABEL']}


@route("/templateprint")
@view('templateprint.jinja2')
def templatePrint():
    templateFiles = [os.path.basename(file) for file in glob.glob('/appconfig/*.lbl')]

    return {
        'files': templateFiles,
        'printers': PRINTERS,
        'website': CONFIG['WEBSITE'],
        'label': CONFIG['LABEL']
    }


#@get('/api/print/template/<templatefile>')
#@post('/api/print/template/<templatefile>')
@route('/api/print/template/<templatefile>', method=['GET', 'POST', 'OPTIONS'])
@enable_cors
def printtemplate(templatefile):
    return_dict = {'Success': False}
    template_data = get_template_data(templatefile)

    try:
        context = get_label_context(request)
    except LookupError as e:
        return_dict['error'] = e.message
        return return_dict

    try:
        payload = request.json
    except json.JSONDecodeError as e:
        payload = None

    im = create_label_from_template(template_data, payload, **context)
    if DEBUG:
        im.save('sample-out.png')

    return instance.print_label(im, **context)

@route('/health', method=['GET', 'POST'])
@enable_cors
def health():
    response.status = '200 OK'
    printers = instance.get_printers()
    response.body = json.dumps({'printers': printers})
    if len(printers) == 0:
        response.status = '500 Internal Server Error'

@route('/api/printer/<printer_name>/media', method=['GET', 'OPTIONS'])
@enable_cors
def get_printer_media(printer_name):
    """
    API endpoint to get media details for a specific printer
    Returns label sizes and default size for the printer
    """
    try:
        label_sizes_list = instance.get_label_sizes(printer_name)
        default_size = instance.get_default_label_size(printer_name)

        # Convert list of tuples to dict for JSON response
        label_sizes_dict = {}
        for item in label_sizes_list:
            if isinstance(item, tuple) and len(item) == 2:
                short, long = item
                label_sizes_dict[short] = long
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                label_sizes_dict[item[0]] = item[1]
            else:
                logger.warning(f"Skipping invalid label size entry in API: {item}")

        return {
            'success': True,
            'label_sizes': label_sizes_dict,
            'default_size': default_size
        }
    except Exception as e:
        response.status = 500
        return {
            'success': False,
            'error': str(e)
        }

def get_template_data(templatefile):
    """
    Deserialize data from a template file that may contain either JSON or YAML content.

    Parameters:
        templatefile (str): Path to the file.

    Returns:
        data (dict): Deserialized data structure.
    """
    try:
        with open('/appconfig/' + templatefile, 'r') as file:
            # Try to parse the file as JSON
            try:
                data = json.load(file)
                return data
            except json.JSONDecodeError:
                # If JSON parsing fails, attempt YAML parsing
                file.seek(0)  # Reset file pointer to the beginning
                data = yaml.safe_load(file)
                return data
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def create_label_from_template(template, payload, **kwargs):
    width, height = instance.get_label_width_height(ElementBase.get_value(template, kwargs, 'font_path'), **kwargs)
    width = template.get('width', width)
    height = template.get('height', height)
    dimensions = width, height

    margin_left = ElementBase.get_value(template, kwargs, 'margin_left', 15)
    margin_top = ElementBase.get_value(template, kwargs, 'margin_top', 22)
    margin_right = ElementBase.get_value(template, kwargs, 'margin_right', margin_left)
    margin_bottom = ElementBase.get_value(template, kwargs, 'margin_bottom', margin_top)
    margins = [margin_left, margin_top, margin_right, margin_bottom]

    im = Image.new('RGBA', (width, height), 'white')
    draw = ImageDraw.Draw(im)

    elements = template.get('elements', [])

    for element in elements:
        ElementBase.process_with_plugins(element, im, margins, dimensions, payload, **kwargs)

    return im

def get_label_context(request):
    """ might raise LookupError() """

    d = request.params.decode()  # UTF-8 decoded form data

    # Get printer name early to use for printer-specific defaults
    printer_name = d.get('printer', None)

    provided_font_family = d.get('font_family')
    if provided_font_family is not None:
        font_family = provided_font_family.rpartition('(')[0].strip()
        font_style = provided_font_family.rpartition('(')[2].rstrip(')')
    else:
        default_fonts = CONFIG.get('LABEL')
        font_family = CONFIG['LABEL']['DEFAULT_FONTS']['family']
        font_style = CONFIG['LABEL']['DEFAULT_FONTS']['style']

    context = {
        'text': d.get('text', None),
        'font_size': int(d.get('font_size', 40)),
        'font_family': font_family,
        'font_style': font_style,
        'label_size': d.get('label_size', instance.get_default_label_size(printer_name)),
        'kind': instance.get_label_kind(d.get('label_size', instance.get_default_label_size(printer_name)), printer_name),
        'margin': int(d.get('margin', 10)),
        'threshold': int(d.get('threshold', 70)),
        'align': d.get('align', 'left'),
        'orientation': d.get('orientation', 'standard'),
        'margin_top': float(d.get('margin_top', 24)) / 100.,
        'margin_bottom': float(d.get('margin_bottom', 45)) / 100.,
        'margin_left': float(d.get('margin_left', 35)) / 100.,
        'margin_right': float(d.get('margin_right', 35)) / 100.,
        'grocycode': d.get('grocycode', None),
        'product': d.get('product', None),
        'duedate': d.get('due_date', d.get('duedate', None)),
        'printer': printer_name,
        'quantity': d.get('quantity', 1),
    }
    context['margin_top'] = int(context['font_size'] * context['margin_top'])
    context['margin_bottom'] = int(context['font_size'] * context['margin_bottom'])
    context['margin_left'] = int(context['font_size'] * context['margin_left'])
    context['margin_right'] = int(context['font_size'] * context['margin_right'])

    context['fill_color'] = (255, 0, 0) if 'red' in context['label_size'] else (0, 0, 0)

    def get_font_path(font_family_name, font_style_name):
        try:
            if font_family_name is None or font_style_name is None or not font_family_name in FONTS or not font_style_name in \
                                                                                                           FONTS[
                                                                                                               font_family_name]:
                font_family_name = CONFIG['LABEL']['DEFAULT_FONTS']['family']
                font_style_name = CONFIG['LABEL']['DEFAULT_FONTS']['style']
            font_path = FONTS[font_family_name][font_style_name]
        except KeyError:
            raise LookupError("Couln't find the font & style")
        return font_path

    context['font_path'] = get_font_path(context['font_family'], context['font_style'])

    # Get label dimensions for the specific printer
    printer_name = context.get('printer')
    width, height = instance.get_label_dimensions(context['label_size'], printer_name)
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
    linesize = im_font.getlength(text)
    textsize = draw.multiline_textbbox((0, 0), text, font=im_font)
    textsize = (textsize[2], textsize[3])
    width, height = instance.get_label_width_height(textsize, **kwargs)
    adjusted_text_size = ElementBase.adjust_font_to_fit(draw, kwargs['font_path'], kwargs['font_size'], text, (width, height), 2,
                                            kwargs['margin_left'] + kwargs['margin_right'],
                                            kwargs['margin_top'] + kwargs['margin_bottom'],
                                            kwargs['align'])
    if adjusted_text_size != textsize:
        im_font = ImageFont.truetype(kwargs['font_path'], adjusted_text_size)
    im = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(im)
    offset = instance.get_label_offset(width, height, textsize, **kwargs)
    draw.multiline_text(offset, text, kwargs['fill_color'], font=im_font, align=kwargs['align'])
    return im


def create_label_grocy(text, **kwargs):
    product = kwargs['product']
    duedate = kwargs['duedate']
    grocycode = kwargs['grocycode']
    margin_left = 15  #kwargs['margin_left']
    margin_top = 22  #kwargs['margin_top']
    margin_right = margin_left  #kwargs['margin_right']
    margin_bottom = margin_top  #kwargs['margin_bottom']

    wrapper = textwrap.TextWrapper(width=25)
    product = "\n".join(wrapper.wrap(text=product))

    # prepare grocycode datamatrix
    from pylibdmtx.pylibdmtx import encode
    encoded = encode(grocycode.encode('utf8'),
                     size="SquareAuto")  # adjusted for 300x300 dpi - results in DM code roughly 5x5mm
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

    im.paste(datamatrix,
             (horizontal_offset, vertical_offset, horizontal_offset + encoded.width, vertical_offset + encoded.height))

    if kwargs['orientation'] == 'standard':
        vertical_offset += -10
        horizontal_offset = encoded.width + 40
    elif kwargs['orientation'] == 'rotated':
        vertical_offset += encoded.width + 40
        horizontal_offset += -10

    textoffset = horizontal_offset, vertical_offset
    adjusted_product_font_size = ElementBase.adjust_font_to_fit(draw, kwargs['font_path'], kwargs['font_size'], product,
                                                    (width, height), 2, horizontal_offset + margin_right,
                                                    vertical_offset + margin_bottom)
    if kwargs['font_size'] != adjusted_product_font_size:
        product_font = ImageFont.truetype(kwargs['font_path'], adjusted_product_font_size)

    draw.text(textoffset, product, kwargs['fill_color'], font=product_font)

    if duedate is not None:
        additional_offset = draw.multiline_textbbox((0, 0), product, font=product_font)[3] + 10

        if kwargs['orientation'] == 'standard':
            vertical_offset += additional_offset
            #horizontal_offset = margin_left
        elif kwargs['orientation'] == 'rotated':
            #vertical_offset = margin_left
            horizontal_offset += additional_offset
        textoffset = horizontal_offset, vertical_offset

        adjusted_duedate_font_size = ElementBase.adjust_font_to_fit(draw, kwargs['font_path'], kwargs['font_size'], duedate,
                                                        (width, height), 2, horizontal_offset + margin_right,
                                                        vertical_offset + margin_bottom)
        duedate_font = ImageFont.truetype(kwargs['font_path'], adjusted_duedate_font_size)

        draw.text(textoffset, duedate, kwargs['fill_color'], font=duedate_font)

    return im


@get('/api/preview/text')
@post('/api/preview/text')
@enable_cors
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
@enable_cors
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


@route('/api/preview/template/<templatefile>', method=['GET', 'POST', 'OPTIONS'])
@enable_cors
def get_preview_template_image(templatefile):
    context = get_label_context(request)
    template_data = get_template_data(templatefile)

    try:
        payload = request.json
    except json.JSONDecodeError as e:
        payload = None

    im = create_label_from_template(template_data, payload, **context)
    return_format = request.query.get('return_format', 'png')
    if return_format == 'base64':
        import base64
        response.set_header('Content-type', 'text/plain')
        return base64.b64encode(image_to_png_bytes(im))
    else:
        response.set_header('Content-type', 'image/png')
        return image_to_png_bytes(im)

@route('/api/template/<templatefile>/fields', method=['GET', 'OPTIONS'])
@enable_cors
def get_template_fields(templatefile):
    """
    API endpoint to get form fields required by a template
    Returns a JSON object with field definitions
    """
    template_data = get_template_data(templatefile)
    if not template_data:
        response.status = 404
        return {'error': 'Template not found'}

    fields = []

    def extract_fields_from_elements(elements):
        for element in elements:
            form_elements = ElementBase.get_form_elements_with_plugins(element)
            if form_elements is not None:
                fields.extend(form_elements)

    if 'elements' in template_data:
        extract_fields_from_elements(template_data['elements'])

    return {
        'template_name': template_data.get('name', templatefile),
        'fields': fields
    }

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
    return_dict = {'success': False}

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
    global DEBUG, FONTS, BACKEND_CLASS, CONFIG, LABEL_SIZES, PRINTERS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', default=False)
    parser.add_argument('--loglevel', type=lambda x: getattr(logging, x.upper()), default=False)
    parser.add_argument('--font-folder', default=False, help='folder for additional .ttf/.otf fonts')
    #parser.add_argument('--default-label-size', default=False, help='Label size inserted in your printer. Defaults to 62.')
    #parser.add_argument('--default-orientation', default=False, choices=('standard', 'rotated'), help='Label orientation, defaults to "standard". To turn your text by 90°, state "rotated".')
    #parser.add_argument('printer',  nargs='?', default=False, help='String descriptor for the printer to use (like tcp://192.168.0.23:9100 or file:///dev/usb/lp0)')
    args = parser.parse_args()

    #if args.printer:
    #    CONFIG['PRINTER']['PRINTER'] = args.printer

    if args.port:
        PORT = args.port
    else:
        PORT = 8013  # CONFIG['SERVER']['PORT']

    if args.loglevel:
        LOGLEVEL = args.loglevel
    else:
        LOGLEVEL = CONFIG['SERVER']['LOGLEVEL']

    if LOGLEVEL == 'DEBUG':
        DEBUG = True
    else:
        DEBUG = False

    instance.DEBUG = DEBUG

    #if args.model:
    #    CONFIG['PRINTER']['MODEL'] = args.model

    #if args.default_label_size:
    #    CONFIG['LABEL']['DEFAULT_SIZE'] = args.default_label_size

    #if args.default_orientation:
    #    CONFIG['LABEL']['DEFAULT_ORIENTATION'] = args.default_orientation

    if args.font_folder:
        ADDITIONAL_FONT_FOLDER = args.font_folder
    else:
        ADDITIONAL_FONT_FOLDER = '/fonts_folder'

    logging.basicConfig(level=LOGLEVEL)
    instance.logger = logger
    instance.CONFIG = CONFIG

    initialization_errors = instance.initialize(CONFIG)
    if len(initialization_errors) > 0:
        parser.error(initialization_errors)

    # Get label sizes as list of tuples and convert to dict
    label_sizes_list = instance.get_label_sizes()
    LABEL_SIZES = {}
    for item in label_sizes_list:
        if isinstance(item, tuple) and len(item) == 2:
            short, long = item
            LABEL_SIZES[short] = long
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            LABEL_SIZES[item[0]] = item[1]
        else:
            logger.warning(f"Skipping invalid label size entry: {item}")

    PRINTERS = instance.get_printers()

    # Get default size from printer first, then fall back to config
    default_size = instance.get_default_label_size()
    if default_size and default_size in LABEL_SIZES.keys():
        CONFIG['LABEL']['DEFAULT_SIZE'] = default_size
    elif CONFIG['LABEL']['DEFAULT_SIZE'] not in LABEL_SIZES.keys():
        parser.error(
            "Invalid --default-label-size. Please choose one of the following:\n:" + " ".join(list(LABEL_SIZES.keys())))

    FONTS = get_fonts()
    FONTS.update(get_fonts(ADDITIONAL_FONT_FOLDER))

    if not FONTS:
        sys.stderr.write("Not a single font was found on your system. Please install some into the '+ ADDITIONAL_FONT_FOLDER +'.\n")
        sys.exit(2)

    for font in CONFIG['LABEL']['DEFAULT_FONTS']:
        try:
            FONTS[font['family']][font['style']]
            CONFIG['LABEL']['DEFAULT_FONTS'] = font
            logger.debug("Selected the following default font: {}".format(font))
            break
        except:
            pass
    if CONFIG['LABEL']['DEFAULT_FONTS'] is None:
        sys.stderr.write('Could not find any of the default fonts. Choosing a random one.\n')
        family = random.choice(list(FONTS.keys()))
        style = random.choice(list(FONTS[family].keys()))
        CONFIG['LABEL']['DEFAULT_FONTS'] = {'family': family, 'style': style}
        sys.stderr.write(
            'The default font is now set to: {family} ({style})\n'.format(**CONFIG['LABEL']['DEFAULT_FONTS']))

    run(host=CONFIG['SERVER']['HOST'], port=PORT, debug=DEBUG)


if __name__ == "__main__":
    main()
