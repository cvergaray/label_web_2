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
    with open('config.minimal.json', encoding='utf-8') as fh:
        CONFIG = json.load(fh)
        print("loaded config from config.minimal.json")

PRINTERS = None
LABEL_SIZES = None
CONFIG_FILE = '/appconfig/config.json'


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


def label_sizes_list_to_dict(label_sizes_list, logger=None, warn_prefix=""):
    """
    Convert a list of label size tuples/lists to a dict.
    Optionally logs warnings for invalid entries.

    Args:
        label_sizes_list: List of tuples/lists where each item is (short_name, long_name)
        logger: Optional logger instance for warnings
        warn_prefix: Optional prefix for warning messages

    Returns:
        dict: Dictionary mapping short names to long names
    """
    label_sizes_dict = {}
    for item in label_sizes_list:
        if isinstance(item, tuple) and len(item) == 2:
            short, long = item
            label_sizes_dict[short] = long
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            label_sizes_dict[item[0]] = item[1]
        else:
            if logger:
                logger.warning(f"{warn_prefix}Skipping invalid label size entry: {item}")
    return label_sizes_dict


def reload_config():
    """Reload CONFIG from file."""
    global CONFIG
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            CONFIG = json.load(f)
            logger.info(f"Reloaded config from {CONFIG_FILE}")
            return True
    except FileNotFoundError:
        try:
            with open('config.minimal.json', 'r', encoding='utf-8') as f:
                CONFIG = json.load(f)
                logger.info("Reloaded config from config.minimal.json")
                return True
        except Exception as e:
            logger.error(f"Error reloading config: {e}")
            return False
    except Exception as e:
        logger.error(f"Error reloading config: {e}")
        return False


def save_config(new_config):
    """Save CONFIG to file."""
    global CONFIG
    try:
        # Ensure the directory exists (for /appconfig)
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=2, ensure_ascii=False)
        CONFIG = new_config
        logger.info(f"Config saved to {CONFIG_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False


def config_to_settings_format(config):
    """Convert CONFIG to the settings format expected by frontend."""
    default_font = config.get('LABEL', {}).get('DEFAULT_FONTS', [{}])
    if isinstance(default_font, list) and len(default_font) > 0:
        default_font = default_font[0]
    else:
        default_font = {}

    # Normalize LABEL_SIZES to a dict mapping for UI
    cfg_sizes = config.get('PRINTER', {}).get('LABEL_SIZES', {})
    if isinstance(cfg_sizes, list):
        # list of [key, label] pairs
        label_sizes_map = {k: v for k, v in cfg_sizes}
    elif isinstance(cfg_sizes, dict):
        label_sizes_map = dict(cfg_sizes)
    else:
        label_sizes_map = {}

    return {
        'server': {
            'host': config.get('SERVER', {}).get('HOST', ''),
            'logLevel': config.get('SERVER', {}).get('LOGLEVEL', 'INFO'),
            'additionalFontFolder': config.get('SERVER', {}).get('ADDITIONAL_FONT_FOLDER', False)
        },
        'printer': {
            'useCups': config.get('PRINTER', {}).get('USE_CUPS', False),
            'server': config.get('PRINTER', {}).get('SERVER', 'localhost'),
            'printer': config.get('PRINTER', {}).get('PRINTER', ''),
            'enabledSizes': config.get('PRINTER', {}).get('ENABLED_SIZES', {}),
            'labelSizes': label_sizes_map,
            'printersInclude': config.get('PRINTER', {}).get('PRINTERS_INCLUDE', []),
            'printersExclude': config.get('PRINTER', {}).get('PRINTERS_EXCLUDE', []),
        },
        'label': {
            'defaultSize': config.get('LABEL', {}).get('DEFAULT_SIZE', ''),
            'defaultOrientation': config.get('LABEL', {}).get('DEFAULT_ORIENTATION', 'standard'),
            'defaultFontSize': config.get('LABEL', {}).get('DEFAULT_FONT_SIZE', 70),
            'defaultFontFamily': default_font.get('family', 'DejaVu Sans'),
            'defaultFontStyle': default_font.get('style', 'Book')
        },
        'website': {
            'htmlTitle': config.get('WEBSITE', {}).get('HTML_TITLE', 'Label Designer'),
            'pageTitle': config.get('WEBSITE', {}).get('PAGE_TITLE', 'Label Designer'),
            'pageHeadline': config.get('WEBSITE', {}).get('PAGE_HEADLINE', 'Design and print labels')
        }
    }


def settings_format_to_config(settings):
    """Convert frontend settings format back to CONFIG structure."""
    # Normalize custom sizes back to CONFIG format (dict)
    label_sizes_map = settings.get('printer', {}).get('labelSizes', {}) or {}

    config = {
        'SERVER': {
            'HOST': settings.get('server', {}).get('host', ''),
            'LOGLEVEL': settings.get('server', {}).get('logLevel', 'INFO'),
            'ADDITIONAL_FONT_FOLDER': settings.get('server', {}).get('additionalFontFolder', False)
        },
        'PRINTER': {
            'USE_CUPS': settings.get('printer', {}).get('useCups', False),
            'SERVER': settings.get('printer', {}).get('server', 'localhost'),
            'PRINTER': settings.get('printer', {}).get('printer', ''),
            'ENABLED_SIZES': settings.get('printer', {}).get('enabledSizes', {}),
            'LABEL_SIZES': label_sizes_map,
            'PRINTERS_INCLUDE': settings.get('printer', {}).get('printersInclude', []),
            'PRINTERS_EXCLUDE': settings.get('printer', {}).get('printersExclude', []),
        },
        'LABEL': {
            'DEFAULT_SIZE': settings.get('label', {}).get('defaultSize', ''),
            'DEFAULT_ORIENTATION': settings.get('label', {}).get('defaultOrientation', 'standard'),
            'DEFAULT_FONT_SIZE': settings.get('label', {}).get('defaultFontSize', 70),
            'DEFAULT_FONTS': [
                {
                    'family': settings.get('label', {}).get('defaultFontFamily', 'DejaVu Sans'),
                    'style': settings.get('label', {}).get('defaultFontStyle', 'Book')
                }
            ]
        },
        'WEBSITE': {
            'HTML_TITLE': settings.get('website', {}).get('htmlTitle', 'Label Designer'),
            'PAGE_TITLE': settings.get('website', {}).get('pageTitle', 'Label Designer'),
            'PAGE_HEADLINE': settings.get('website', {}).get('pageHeadline', 'Design and print labels')
        }
    }

    # Preserve any existing config sections not managed by settings UI
    if 'LABEL_SIZES' in CONFIG.get('PRINTER', {}):
        # merge existing with new (new wins)
        old = CONFIG['PRINTER']['LABEL_SIZES']
        if isinstance(old, dict):
            merged = dict(old)
            merged.update(label_sizes_map)
            config['PRINTER']['LABEL_SIZES'] = merged
    if 'LABEL_PRINTABLE_AREA' in CONFIG.get('PRINTER', {}):
        config['PRINTER']['LABEL_PRINTABLE_AREA'] = CONFIG['PRINTER']['LABEL_PRINTABLE_AREA']

    return config


# Filter a list of (key,label) sizes by CONFIG PRINTER.ENABLED_SIZES for given printer.
# If no entry exists for the printer, allow all sizes.
def filter_label_sizes_for_printer(label_sizes_list, printer_name):
    enabled_map = CONFIG.get('PRINTER', {}).get('ENABLED_SIZES', {}) or {}
    enabled_for_printer = enabled_map.get(printer_name)
    if not enabled_for_printer:
        return label_sizes_list
    enabled_set = set(enabled_for_printer)
    return [t for t in label_sizes_list if t[0] in enabled_set]


# Filter printer list by CONFIG PRINTER.PRINTERS_INCLUDE and PRINTERS_EXCLUDE
def filter_printers(printers_list):
    """
    Filter printers based on include/exclude lists.
    If include list has items, only show those printers.
    Then apply exclude list to remove specific printers.
    """
    include = CONFIG.get('PRINTER', {}).get('PRINTERS_INCLUDE', []) or []
    exclude = CONFIG.get('PRINTER', {}).get('PRINTERS_EXCLUDE', []) or []

    filtered = printers_list

    # If include list is specified, only show those printers
    if include:
        filtered = [p for p in filtered if p in include]

    # Apply exclude list
    if exclude:
        filtered = [p for p in filtered if p not in exclude]

    return filtered


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
    # Filter printers for display
    filtered_printers = filter_printers(PRINTERS)
    default_printer = instance.selected_printer if instance.selected_printer else (filtered_printers[0] if filtered_printers else None)
    default_orientation = CONFIG['LABEL'].get('DEFAULT_ORIENTATION', 'standard')

    # Compute label sizes for default printer and filter by enabled
    label_sizes_list = instance.get_label_sizes(default_printer)
    label_sizes_list = filter_label_sizes_for_printer(label_sizes_list, default_printer)
    label_sizes = label_sizes_list_to_dict(label_sizes_list, logger)

    return {'font_family_names': font_family_names,
            'fonts': FONTS,
            'label_sizes': label_sizes,
            'printers': filtered_printers,
            'default_printer': default_printer,
            'default_orientation': default_orientation,
            'website': CONFIG['WEBSITE'],
            'label': CONFIG['LABEL']}


@route('/api/printer/<printer_name>/media', method=['GET', 'OPTIONS'])
@enable_cors
def get_printer_media(printer_name):
    """
    API endpoint to get media details for a specific printer
    Returns label sizes and default size for the printer
    """
    try:
        label_sizes_list = instance.get_label_sizes(printer_name)
        # Filter by enabled sizes
        label_sizes_list = filter_label_sizes_for_printer(label_sizes_list, printer_name)
        default_size = instance.get_default_label_size(printer_name)

        # Convert list of tuples to dict for JSON response
        label_sizes_dict = label_sizes_list_to_dict(label_sizes_list, logger, warn_prefix="API: ")

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


@route("/templateprint")
@view('templateprint.jinja2')
def templatePrint():
    templateFiles = [os.path.basename(file) for file in glob.glob('/appconfig/*.lbl')]
    default_printer = instance.selected_printer if instance.selected_printer else (PRINTERS[0] if PRINTERS else None)

    # Filter label sizes for default printer
    label_sizes_list = instance.get_label_sizes(default_printer)
    label_sizes_list = filter_label_sizes_for_printer(label_sizes_list, default_printer)
    label_sizes = label_sizes_list_to_dict(label_sizes_list, logger)

    return {
        'files': templateFiles,
        'printers': PRINTERS,
        'default_printer': default_printer,
        'label_sizes': label_sizes,
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
        payload = {}

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


@route('/api/template/<templatefile>/raw', method=['GET', 'OPTIONS'])
@enable_cors
def get_template_raw(templatefile):
    """Return the raw contents of a template file as plain text.

    The file is read from /appconfig/<templatefile> inside the container.
    """
    try:
        path = os.path.join('/appconfig', templatefile)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        response.content_type = 'text/plain; charset=utf-8'
        return content
    except FileNotFoundError:
        response.status = 404
        return 'Template not found'
    except Exception as e:
        response.status = 500
        return f'Error reading template: {e}'


@post('/api/template/<templatefile>/raw')
@enable_cors
def save_template_raw(templatefile):
    """Overwrite the raw contents of a template file with the request body.

    Expects the new template content as text/plain in the request body.
    """
    try:
        path = os.path.join('/appconfig', templatefile)

        # Read entire request body as UTF-8 text
        body = request.body.read()
        try:
            content = body.decode('utf-8')
        except AttributeError:
            # In case body is already str (older bottle versions)
            content = body

        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

        response.content_type = 'application/json'
        return json.dumps({'success': True})
    except Exception as e:
        response.status = 500
        response.content_type = 'application/json'
        return json.dumps({'success': False, 'error': str(e)})

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

    # Add any extra parameters from the request that are not already in context
    for param_name, param_value in d.items():
        if param_name not in context:
            context[param_name] = param_value

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


@route('/api/preview/template/<templatefile>', method=['GET', 'POST', 'OPTIONS'])
@enable_cors
def get_preview_template_image(templatefile):
    context = get_label_context(request)
    template_data = get_template_data(templatefile)

    try:
        payload = request.json
    except json.JSONDecodeError as e:
        payload = {}

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


@route("/settings")
@view('settings.jinja2')
def settings_page():
    """Render the settings management page."""
    return {
        'website': CONFIG['WEBSITE'],
        'label': CONFIG['LABEL']
    }


@route('/api/settings', method=['GET', 'OPTIONS'])
@enable_cors
def get_settings():
    """Get current application settings."""
    return config_to_settings_format(CONFIG)


@route('/api/settings', method=['POST', 'OPTIONS'])
@enable_cors
def save_settings_api():
    """Save application settings."""
    try:
        payload = request.json

        # Convert frontend settings format to CONFIG format
        new_config = settings_format_to_config(payload)

        # Merge with existing CONFIG to preserve other settings
        merged_config = {**CONFIG, **new_config}

        if save_config(merged_config):
            # Apply new settings at runtime
            global PRINTERS, LABEL_SIZES
            instance.CONFIG = CONFIG
            instance.initialize(CONFIG)
            PRINTERS = instance.get_printers()
            # Recompute default label sizes list for default printer for global usage
            default_printer = instance.selected_printer if instance.selected_printer else (PRINTERS[0] if PRINTERS else None)
            label_sizes_list = instance.get_label_sizes(default_printer)
            label_sizes_list = filter_label_sizes_for_printer(label_sizes_list, default_printer)
            LABEL_SIZES = label_sizes_list_to_dict(label_sizes_list, logger)
            return {'success': True, 'message': 'Settings saved. Some changes may require app restart.'}
        else:
            response.status = 500
            return {'success': False, 'error': 'Failed to save settings'}
    except Exception as e:
        response.status = 400
        logger.error(f"Error saving settings: {e}")
        return {'success': False, 'error': str(e)}


@route('/api/settings/printers', method=['GET', 'OPTIONS'])
@enable_cors
def get_settings_printers():
    """Get list of printers with their available media sizes."""

    try:
        printers = instance.get_printers() or []
        all_media_sizes = {}

        for printer in printers:
            try:
                media_sizes_list = instance.get_label_sizes(printer)
                all_media_sizes[printer] = media_sizes_list
            except Exception as e:
                logger.warning(f"Could not get media sizes for printer {printer}: {e}")
                all_media_sizes[printer] = []

        return {
            'printers': printers,
            'all_media_sizes': all_media_sizes
        }
    except Exception as e:
        response.status = 500
        logger.error(f"Error getting printers: {e}")
        return {'error': str(e)}


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
    LABEL_SIZES = label_sizes_list_to_dict(label_sizes_list, logger)

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
