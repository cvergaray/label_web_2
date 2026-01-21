#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is a web service to print labels on label printers via CUPS.
"""
import cups
import copy
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

from configuration_management import (
    label_sizes_list_to_dict,
    reload_config,
    save_config,
    config_to_settings_format,
    settings_format_to_config,
    filter_label_sizes_for_printer,
    filter_printers,
    normalize_default_fonts,
    validate_configuration,
    compute_printer_selection,
)

logger = logging.getLogger(__name__)
instance = implementation()

# Initialize CONFIG with a safe default structure
CONFIG = {
    'SERVER': {
        'HOST': '0.0.0.0',
        'PORT': 8013,
        'LOGLEVEL': 'INFO',
        'ADDITIONAL_FONT_FOLDER': '/fonts'
    },
    'PRINTER': {
        'USE_CUPS': True,
        'SERVER': 'localhost',
        'PRINTER': '',
        'LABEL_SIZES': [],
        'ENABLED_SIZES': {},
        'PRINTERS_INCLUDE': [],
        'PRINTERS_EXCLUDE': [],
        'LABEL_PRINTABLE_AREA': {}
    },
    'LABEL': {
        'DEFAULT_SIZE': '62',
        'DEFAULT_ORIENTATION': 'standard',
        'DEFAULT_FONT_SIZE': 70,
        'DEFAULT_FONTS': {'family': 'DejaVu Sans', 'style': 'Book'}
    },
    'WEBSITE': {
        'HTML_TITLE': 'Label Designer',
        'PAGE_TITLE': 'Label Designer',
        'PAGE_HEADLINE': 'Design and print labels'
    }
}

CONFIG_ERRORS = []  # Store configuration validation errors
CONFIG_FILE = '/appconfig/config.json'

# Try to load config file
try:
    with open(CONFIG_FILE, encoding='utf-8') as fh:
        CONFIG = json.load(fh)
        print(f"loaded config from {CONFIG_FILE}")
except FileNotFoundError:
    try:
        with open('config.minimal.json', encoding='utf-8') as fh:
            CONFIG = json.load(fh)
            print("loaded config from config.minimal.json")
    except FileNotFoundError:
        error_msg = "Warning: No config file found. Using default configuration. Please configure settings on the settings page."
        CONFIG_ERRORS.append(error_msg)
        logger.error(error_msg)
except Exception as e:
    error_msg = f"Error: Failed to parse config file: {e}"
    CONFIG_ERRORS.append(error_msg)
    logger.error(error_msg)

PRINTERS = None
LABEL_SIZES = None
FONTS = {}  # Will be populated during initialization


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


# Wrapper for save_config that updates global CONFIG
def save_config_with_global_update(new_config):
    """Save configuration to file and update global CONFIG."""
    global CONFIG
    if save_config(new_config):
        CONFIG.clear()
        CONFIG.update(new_config)
        return True
    return False



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
    filtered_printers, default_printer, label_sizes = compute_printer_selection(instance, PRINTERS, CONFIG, logger)
    # Normalize DEFAULT_FONTS to always be a dict for template compatibility
    label_config = copy.deepcopy(CONFIG['LABEL'])
    label_config['DEFAULT_FONTS'] = normalize_default_fonts(label_config.get('DEFAULT_FONTS', {}))

    return {'font_family_names': font_family_names,
            'fonts': FONTS,
            'label_sizes': label_sizes,
            'printers': filtered_printers,
            'default_printer': default_printer,
            'default_orientation': CONFIG['LABEL'].get('DEFAULT_ORIENTATION', 'standard'),
            'website': CONFIG['WEBSITE'],
            'label': label_config,
            'has_errors': len(CONFIG_ERRORS) > 0}


@route('/api/printer/<printer_name>/media', method=['GET', 'POST', 'OPTIONS'])
@enable_cors
def get_printer_media(printer_name):
    """
    API endpoint to get media details for a specific printer.
    Returns label sizes and default size for the printer.
    Handles URL encoding and special values (empty string, 'null').

    Supports two calling modes:
    - GET: Uses the global CONFIG (backward compatible)
    - POST with config in body: Uses the provided configuration for accurate preview

    Used by labeldesigner and settings pages.
    """
    try:
        # Decode printer_name in case it's URL encoded
        from urllib.parse import unquote
        printer_name = unquote(printer_name) if printer_name else None

        # Handle empty string or 'null' as None (for default printer)
        if printer_name == '' or printer_name == 'null' or printer_name == 'undefined':
            printer_name = None

        # Determine which configuration to use
        instance_to_use = instance

        config_to_use = CONFIG

        # If POST request with config body, use that configuration instead of global CONFIG
        if request.method == 'POST':
            try:
                payload = request.json
                if payload and isinstance(payload, dict):
                    config_to_use = settings_format_to_config(payload)
                    temp_instance = implementation()
                    temp_instance.initialize(config_to_use)
                    instance_to_use = temp_instance
            except Exception as e:
                logger.warning(f"Could not parse config from request body: {e}")
                # Fall back to global CONFIG on error
                instance_to_use = instance
                config_to_use = CONFIG

        # Get label sizes for the printer
        label_sizes_list = instance_to_use.get_label_sizes(printer_name)

        # Filter by enabled sizes using the provided/global configuration
        label_sizes_list = filter_label_sizes_for_printer(label_sizes_list, printer_name, config_to_use)

        # Get default size
        default_size = instance_to_use.get_default_label_size(printer_name)

        # Convert list of tuples to dict for JSON response
        label_sizes_dict = label_sizes_list_to_dict(label_sizes_list, logger, warn_prefix="API: ")

        return {
            'success': True,
            'label_sizes': label_sizes_dict,
            'default_size': default_size
        }
    except Exception as e:
        response.status = 500
        logger.error(f"Error getting printer media: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@route("/templateprint")
@view('templateprint.jinja2')
def templatePrint():
    templateFiles = [os.path.basename(file) for file in glob.glob('/appconfig/*.lbl')]
    # Use shared helper to get printers, default, and label sizes
    filtered_printers, default_printer, label_sizes = compute_printer_selection(instance, PRINTERS, CONFIG, logger)

    # Normalize DEFAULT_FONTS to always be a dict for template compatibility
    label_config = copy.deepcopy(CONFIG['LABEL'])
    label_config['DEFAULT_FONTS'] = normalize_default_fonts(label_config.get('DEFAULT_FONTS', {}))

    return {
        'files': templateFiles,
        'printers': filtered_printers,
        'default_printer': default_printer,
        'label_sizes': label_sizes,
        'website': CONFIG['WEBSITE'],
        'label': label_config,
        'has_errors': len(CONFIG_ERRORS) > 0
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
        # Normalize DEFAULT_FONTS to a dict (config may contain list)
        default_fonts_cfg = normalize_default_fonts(CONFIG.get('LABEL', {}).get('DEFAULT_FONTS', {}))
        font_family = default_fonts_cfg.get('family')
        font_style = default_fonts_cfg.get('style')

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
                # Fallback to normalized defaults if provided font missing
                fallback = normalize_default_fonts(CONFIG.get('LABEL', {}).get('DEFAULT_FONTS', {}))
                font_family_name = fallback.get('family')
                font_style_name = fallback.get('style')
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
    # Normalize DEFAULT_FONTS to always be a dict for template compatibility
    label_config = copy.deepcopy(CONFIG['LABEL'])
    label_config['DEFAULT_FONTS'] = normalize_default_fonts(label_config.get('DEFAULT_FONTS', {}))

    return {
        'website': CONFIG['WEBSITE'],
        'label': label_config,
        'has_errors': len(CONFIG_ERRORS) > 0
    }


@route('/api/config-errors', method=['GET', 'OPTIONS'])
@enable_cors
def get_config_errors():
    """Get list of configuration errors."""
    return {
        'errors': CONFIG_ERRORS,
        'has_errors': len(CONFIG_ERRORS) > 0
    }


@route('/api/settings', method=['GET', 'OPTIONS'])
@enable_cors
def get_settings():
    """Get current application settings."""
    return config_to_settings_format(CONFIG)


@route('/api/settings/validate', method=['POST', 'OPTIONS'])
@enable_cors
def validate_settings_api():
    """Validate settings without saving them."""
    try:
        payload = request.json

        # Convert frontend settings format to CONFIG format
        new_config = settings_format_to_config(payload)

        # Create a temporary instance for validation
        temp_instance = implementation()

        # Try to initialize with the new config
        try:
            temp_instance.initialize(new_config)
        except Exception as init_err:
            return {
                'success': True,
                'has_errors': True,
                'errors': [f"Configuration initialization failed: {init_err}"]
            }

        # Get printers with the new config
        temp_printers = temp_instance.get_printers() or []

        # Get label sizes for ALL printers for comprehensive validation
        all_label_sizes = {}
        for printer in temp_printers:
            try:
                printer_label_sizes_list = temp_instance.get_label_sizes(printer)
                printer_label_sizes_list = filter_label_sizes_for_printer(printer_label_sizes_list, printer, new_config)
                printer_label_sizes = label_sizes_list_to_dict(printer_label_sizes_list, logger)
                all_label_sizes[printer] = printer_label_sizes
            except Exception as e:
                logger.warning(f"Could not get label sizes for printer {printer} during validation: {e}")
                all_label_sizes[printer] = {}

        # Combine all label sizes from all printers for validation
        combined_label_sizes = {}
        for printer_sizes in all_label_sizes.values():
            combined_label_sizes.update(printer_sizes)

        # Get fonts for validation
        temp_fonts = get_fonts()
        additional_folder = new_config.get('SERVER', {}).get('ADDITIONAL_FONT_FOLDER', False)
        if additional_folder:
            temp_fonts.update(get_fonts(additional_folder))

        # Run configuration validation with new_config
        validation_errors = validate_configuration(temp_fonts, combined_label_sizes, temp_printers, new_config)

        # Append initialization errors to the validation errors
        if temp_instance.initialization_errors:
            validation_errors.extend(temp_instance.initialization_errors)

        return {
            'success': True,
            'has_errors': len(validation_errors) > 0,
            'errors': validation_errors
        }
    except Exception as e:
        logger.error(f"Error validating settings: {e}")
        return {
            'success': True,
            'has_errors': True,
            'errors': [f"Validation error: {str(e)}"]
        }


@route('/api/settings', method=['POST', 'OPTIONS'])
@enable_cors
def save_settings_api():
    """Save application settings."""
    try:
        payload = request.json

        # Convert frontend settings format to CONFIG format
        new_config = settings_format_to_config(payload)

        # Merge with existing CONFIG to preserve other settings (use deep copy to avoid mutating CONFIG)
        merged_config = copy.deepcopy(CONFIG)

        # Ensure critical sections exist before update
        for section in ['SERVER', 'PRINTER', 'LABEL', 'WEBSITE']:
            if section not in merged_config:
                merged_config[section] = {}

        # Deep merge to avoid completely replacing sections
        for section, values in new_config.items():
            if section not in merged_config:
                merged_config[section] = values
            elif isinstance(values, dict):
                merged_config[section].update(values)
            else:
                merged_config[section] = values

        if save_config_with_global_update(merged_config):
            # Apply new settings at runtime and revalidate
            global PRINTERS, LABEL_SIZES, CONFIG_ERRORS, FONTS
            instance.CONFIG = CONFIG
            instance.initialize(CONFIG)
            PRINTERS = instance.get_printers()
            default_printer = instance.selected_printer if instance.selected_printer else (PRINTERS[0] if PRINTERS else None)
            label_sizes_list = instance.get_label_sizes(default_printer)
            label_sizes_list = filter_label_sizes_for_printer(label_sizes_list, default_printer, CONFIG)
            LABEL_SIZES = label_sizes_list_to_dict(label_sizes_list, logger)

            # Reload fonts in case the font folder changed
            FONTS = get_fonts()
            additional_folder = CONFIG.get('SERVER', {}).get('ADDITIONAL_FONT_FOLDER', False)
            if additional_folder:
                FONTS.update(get_fonts(additional_folder))

            # Re-run configuration validation
            CONFIG_ERRORS = []
            validation_errors = validate_configuration(FONTS, LABEL_SIZES, PRINTERS, CONFIG)
            CONFIG_ERRORS.extend(validation_errors)

            # Append initialization errors to the configuration errors
            if instance.initialization_errors:
                CONFIG_ERRORS.extend(instance.initialization_errors)

            return {
                'success': True,
                'message': 'Settings saved. Some changes may require app restart.',
                'has_errors': len(CONFIG_ERRORS) > 0,
                'errors': CONFIG_ERRORS
            }
        else:
            response.status = 500
            return {'success': False, 'error': 'Failed to save settings'}
    except Exception as e:
        response.status = 400
        logger.error(f"Error saving settings: {e}")
        return {'success': False, 'error': str(e)}


@route('/api/settings/cups/validate', method=['POST', 'OPTIONS'])
@enable_cors
def validate_cups_server_api():
    """Validate connectivity to a CUPS server without changing current config."""
    try:
        payload = request.json or {}
        server = payload.get('server') or 'localhost'
        old_server = cups.getServer()
        try:
            conn = cups.Connection(server)
            printers = list(conn.getPrinters().keys())
            return {'success': True, 'server': server, 'printers': printers}
        except Exception as e:
            response.status = 400
            return {'success': False, 'error': str(e), 'server': server}
        finally:
            cups.setServer(old_server)
    except Exception as e:
        response.status = 500
        logger.error(f"Error validating CUPS server: {e}")
        return {'success': False, 'error': str(e)}


@route('/api/settings/printers', method=['GET', 'POST', 'OPTIONS'])
@enable_cors
def get_settings_printers():
    """Get list of printers with their available media sizes. Optional config override.

    Query/Body Parameters:
    - include_disabled (GET) or include_disabled (POST body): If true, returns all available
      media sizes without filtering by enabled sizes. Used by settings page to show all
      media that can be enabled/disabled.
    """
    try:
        # Try to get full config from POST body
        preview_config = None
        include_disabled = False

        if request.method == 'POST':
            try:
                payload = request.json
                if payload and isinstance(payload, dict):
                    # Convert frontend settings format to CONFIG format
                    preview_config = settings_format_to_config(payload)
                    # Check for include_disabled flag in POST body
                    include_disabled = payload.get('_include_disabled', False)
            except Exception as e:
                logger.warning(f"Could not parse config from request body: {e}")

        # Fall back to query parameters for backward compatibility
        if preview_config is None:
            use_cups_param = request.query.get('use_cups')
            server_param = request.query.get('server')
            include_disabled = request.query.get('include_disabled') == '1'

            # Use existing CONFIG as base
            preview_config = copy.deepcopy(CONFIG)

            # Ensure PRINTER section exists and is a dict (defensive check)
            if preview_config.get('PRINTER') is None:
                preview_config['PRINTER'] = {}

            # Apply query parameter overrides if provided
            if use_cups_param is not None:
                preview_config['PRINTER']['USE_CUPS'] = use_cups_param == '1'

            if server_param is not None:
                preview_config['PRINTER']['SERVER'] = server_param
        else:
            # For POST requests, also check query params for include_disabled
            include_disabled = include_disabled or request.query.get('include_disabled') == '1'

        # Create a temporary instance for preview (doesn't modify global state)
        temp_instance = implementation()

        # Initialize temporary instance with the preview config
        temp_instance.initialize(preview_config)

        printers = temp_instance.get_printers() or []
        all_media_sizes = {}

        for printer in printers:
            try:
                media_sizes_list = temp_instance.get_label_sizes(printer)
                # Apply filtering based on the preview config, unless include_disabled is set
                if not include_disabled:
                    media_sizes_list = filter_label_sizes_for_printer(media_sizes_list, printer, preview_config)
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


@route('/api/settings/fonts', method=['GET', 'OPTIONS'])
@enable_cors
def get_settings_fonts():
    """Get list of available fonts and their styles."""
    try:
        # Return fonts as { family: [style1, style2, ...] }
        fonts_dict = {}
        for family, styles in FONTS.items():
            fonts_dict[family] = list(styles.keys())

        return {
            'success': True,
            'fonts': fonts_dict
        }
    except Exception as e:
        response.status = 500
        logger.error(f"Error getting fonts: {e}")
        return {'success': False, 'error': str(e)}


@route('/api/settings/fonts/reload', method=['POST', 'OPTIONS'])
@enable_cors
def reload_fonts_api():
    """Reload fonts from the system."""
    try:
        global FONTS

        # Reload fonts from system
        FONTS = get_fonts()

        # Also reload from additional font folder if configured
        additional_folder = CONFIG.get('SERVER', {}).get('ADDITIONAL_FONT_FOLDER', False)
        if additional_folder:
            FONTS.update(get_fonts(additional_folder))

        logger.info(f"Fonts reloaded. Found {len(FONTS)} font families.")

        # Return the updated fonts list
        fonts_dict = {}
        for family, styles in FONTS.items():
            fonts_dict[family] = list(styles.keys())

        return {
            'success': True,
            'fonts': fonts_dict,
            'message': f'Successfully reloaded {len(FONTS)} font families.'
        }
    except Exception as e:
        response.status = 500
        logger.error(f"Error reloading fonts: {e}")
        return {'success': False, 'error': str(e)}


def main():
    global DEBUG, FONTS, BACKEND_CLASS, CONFIG, LABEL_SIZES, PRINTERS, CONFIG_ERRORS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', default=False)
    parser.add_argument('--loglevel', type=lambda x: getattr(logging, x.upper()), default=False)
    parser.add_argument('--font-folder', default=False, help='folder for additional .ttf/.otf fonts')
    args = parser.parse_args()

    if args.port:
        PORT = args.port
    else:
        PORT = 8013  # CONFIG['SERVER']['PORT']

    if args.loglevel:
        LOGLEVEL = args.loglevel
    else:
        LOGLEVEL = CONFIG['SERVER'].get('LOGLEVEL', 'INFO')

    if LOGLEVEL == 'DEBUG':
        DEBUG = True
    else:
        DEBUG = False

    instance.DEBUG = DEBUG

    if args.font_folder:
        ADDITIONAL_FONT_FOLDER = args.font_folder
    else:
        ADDITIONAL_FONT_FOLDER = '/fonts_folder'

    logging.basicConfig(level=LOGLEVEL)
    instance.logger = logger
    instance.CONFIG = CONFIG

    try:
        initialization_errors = instance.initialize(CONFIG)
        if len(initialization_errors) > 0:
            CONFIG_ERRORS.extend(initialization_errors)
            logger.warning(f"Initialization errors: {initialization_errors}")

        # Get label sizes as list of tuples and convert to dict
        label_sizes_list = instance.get_label_sizes()
        LABEL_SIZES = label_sizes_list_to_dict(label_sizes_list, logger)

        PRINTERS = instance.get_printers()

        if len(LABEL_SIZES) == 0:
            error_msg = "No label sizes detected from printer drivers. Please ensure printers are correctly configured or add custom label sizes in settings."
            CONFIG_ERRORS.append(error_msg)
            logger.warning(error_msg)

        # Get default size from printer first, then fall back to config
        default_size = instance.get_default_label_size()
        if default_size and default_size in LABEL_SIZES.keys():
            CONFIG['LABEL']['DEFAULT_SIZE'] = default_size
        elif CONFIG['LABEL'].get('DEFAULT_SIZE') is None or CONFIG['LABEL'].get('DEFAULT_SIZE') not in LABEL_SIZES.keys():
            error_msg = f"Invalid default label size '{CONFIG['LABEL'].get('DEFAULT_SIZE')}'. Please choose one of the following: {', '.join(list(LABEL_SIZES.keys()))}"
            CONFIG_ERRORS.append(error_msg)
            logger.warning(error_msg)

        FONTS = get_fonts()
        FONTS.update(get_fonts(ADDITIONAL_FONT_FOLDER))

        if not FONTS:
            error_msg = f"Not a single font was found on your system. Please install some fonts to the system or configure additional font folder ('{ADDITIONAL_FONT_FOLDER}')."
            CONFIG_ERRORS.append(error_msg)
            logger.error(error_msg)

        # Validate and prepare DEFAULT_FONTS
        # DEFAULT_FONTS should be a list of font dicts from CONFIG
        default_fonts_list = CONFIG.get('LABEL', {}).get('DEFAULT_FONTS', [])

        # Ensure it's a list
        if isinstance(default_fonts_list, dict):
            # If it's a single dict, convert to list
            default_fonts_list = [default_fonts_list]
            CONFIG['LABEL']['DEFAULT_FONTS'] = default_fonts_list
        elif not isinstance(default_fonts_list, list):
            default_fonts_list = []
            CONFIG['LABEL']['DEFAULT_FONTS'] = default_fonts_list

        # Find first font that exists in the system
        selected_font = None
        for font in default_fonts_list:
            family = font.get('family')
            style = font.get('style')
            if family and style and family in FONTS and style in FONTS.get(family, {}):
                # Font exists in system
                selected_font = font
                logger.debug(f"Using configured default font: {family} ({style})")
                break

        # If no configured font was found on system, try to find a reasonable fallback
        if selected_font is None:
            if default_fonts_list:
                # Keep the first configured font even if not available (it might be installed later)
                logger.warning(f"Configured default font '{default_fonts_list[0].get('family')} ({default_fonts_list[0].get('style')})' not found in system. Using it anyway, but UI will show first available.")
                selected_font = default_fonts_list[0]
            else:
                # No default font configured, pick a random one from system
                if FONTS:
                    logger.warning("No default font configured. Choosing a random font from system.")
                    family = random.choice(list(FONTS.keys()))
                    style = random.choice(list(FONTS[family].keys()))
                    selected_font = {'family': family, 'style': style}
                    CONFIG['LABEL']['DEFAULT_FONTS'] = [selected_font]
                    logger.debug(f"Selected random default font: {family} ({style})")
                else:
                    # No fonts available at all
                    selected_font = {'family': 'Unknown', 'style': 'Regular'}
                    CONFIG['LABEL']['DEFAULT_FONTS'] = [selected_font]

        # Store the selected font as a single dict (for backward compatibility with template)
        if selected_font:
            CONFIG['LABEL']['DEFAULT_FONTS'] = selected_font
            logger.debug("Selected the following default font: {}".format(selected_font))
        else:
            # Fallback to empty dict if no font was selected
            CONFIG['LABEL']['DEFAULT_FONTS'] = {'family': '', 'style': ''}

        # Run validation and collect any validation errors
        validation_errors = validate_configuration(FONTS, LABEL_SIZES, PRINTERS, CONFIG)
        CONFIG_ERRORS.extend(validation_errors)

        # Append initialization errors
        if instance.initialization_errors:
            CONFIG_ERRORS.extend(instance.initialization_errors)

    except Exception as e:
        error_msg = f"Critical error during initialization: {str(e)}"
        CONFIG_ERRORS.append(error_msg)
        logger.error(error_msg, exc_info=True)
        # Continue to start the server anyway so user can see errors on settings page
        # Initialize with safe defaults
        if LABEL_SIZES is None:
            LABEL_SIZES = {}
        if PRINTERS is None:
            PRINTERS = []
        if not FONTS:
            FONTS = {}

    run(host=CONFIG['SERVER'].get('HOST', '0.0.0.0'), port=PORT, debug=DEBUG)


if __name__ == "__main__":
    main()
