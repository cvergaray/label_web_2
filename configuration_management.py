#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration management utilities for Label Web.

This module provides helper functions for managing application configuration,
including loading, saving, validation, and format conversion.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

# Configuration file path
CONFIG_FILE = '/appconfig/config.json'

# Default configuration structure
DEFAULT_CONFIG = {
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


def reload_config(config):
    """
    Reload CONFIG from file.

    Args:
        config: Current config dict to update (passed by reference)

    Returns:
        bool: True if successfully reloaded, False otherwise
    """
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)
            config.clear()
            config.update(loaded_config)
            logger.info(f"Reloaded config from {CONFIG_FILE}")
            return True
    except FileNotFoundError:
        try:
            with open('config.minimal.json', 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                config.clear()
                config.update(loaded_config)
                logger.info("Reloaded config from config.minimal.json")
                return True
        except Exception as e:
            logger.error(f"Error reloading config: {e}")
            return False
    except Exception as e:
        logger.error(f"Error reloading config: {e}")
        return False


def save_config(new_config):
    """
    Save CONFIG to file.

    Args:
        new_config: Configuration dictionary to save

    Returns:
        bool: True if successfully saved, False otherwise
    """
    try:
        # Ensure the directory exists (for /appconfig)
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=2, ensure_ascii=False)
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
            'additionalFontFolder': config.get('SERVER', {}).get('ADDITIONAL_FONT_FOLDER', '/fonts')
        },
        'printer': {
            'useCups': config.get('PRINTER', {}).get('USE_CUPS', True),
            'server': config.get('PRINTER', {}).get('SERVER', 'localhost'),
            'printer': config.get('PRINTER', {}).get('PRINTER', ''),
            'enabledSizes': config.get('PRINTER', {}).get('ENABLED_SIZES', {}),
            'labelSizes': label_sizes_map,
            'labelPrintableArea': config.get('PRINTER', {}).get('LABEL_PRINTABLE_AREA', {}),
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
    label_printable_area = settings.get('printer', {}).get('labelPrintableArea', {}) or {}

    config = {
        'SERVER': {
            'HOST': settings.get('server', {}).get('host', ''),
            'LOGLEVEL': settings.get('server', {}).get('logLevel', 'INFO'),
            'ADDITIONAL_FONT_FOLDER': settings.get('server', {}).get('additionalFontFolder', '/fonts')
        },
        'PRINTER': {
            'USE_CUPS': settings.get('printer', {}).get('useCups', True),
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

    # Add LABEL_PRINTABLE_AREA if there are custom dimensions
    if label_printable_area:
        config['PRINTER']['LABEL_PRINTABLE_AREA'] = label_printable_area

    return config


def filter_label_sizes_for_printer(label_sizes_list, printer_name, config):
    """
    Filter a list of (key,label) sizes by CONFIG PRINTER.ENABLED_SIZES for given printer.
    If no entry exists for the printer, allow all sizes.

    Args:
        label_sizes_list: List of (key, label) tuples
        printer_name: Name of the printer to filter for
        config: Configuration dictionary

    Returns:
        list: Filtered list of label sizes
    """
    enabled_map = config.get('PRINTER', {}).get('ENABLED_SIZES', {}) or {}
    enabled_for_printer = enabled_map.get(printer_name)
    if not enabled_for_printer:
        return label_sizes_list
    enabled_set = set(enabled_for_printer)
    return [t for t in label_sizes_list if t[0] in enabled_set]


def filter_printers(printers_list, config):
    """
    Filter printer list by CONFIG PRINTER.PRINTERS_INCLUDE and PRINTERS_EXCLUDE.

    If include list has items, only show those printers.
    Then apply exclude list to remove specific printers.

    Args:
        printers_list: List of printer names
        config: Configuration dictionary

    Returns:
        list: Filtered list of printer names
    """
    include = config.get('PRINTER', {}).get('PRINTERS_INCLUDE', []) or []
    exclude = config.get('PRINTER', {}).get('PRINTERS_EXCLUDE', []) or []

    filtered = printers_list

    # If include list is specified, only show those printers
    if include:
        filtered = [p for p in filtered if p in include]

    # Apply exclude list
    if exclude:
        filtered = [p for p in filtered if p not in exclude]

    return filtered


def normalize_default_fonts(fonts_value):
    """
    Normalize DEFAULT_FONTS to always be a dict.

    Args:
        fonts_value: Can be a dict, list of dicts, or other value

    Returns:
        dict: Normalized font dict with 'family' and 'style' keys, or empty dict
    """
    if isinstance(fonts_value, list):
        # If it's a list, take the first element
        return fonts_value[0] if fonts_value else {}
    elif isinstance(fonts_value, dict):
        return fonts_value
    else:
        return {}


def validate_configuration(fonts_dict, label_sizes_dict, printers_list, config):
    """
    Validate configuration and collect errors without failing startup.

    Args:
        fonts_dict: Dictionary of available fonts
        label_sizes_dict: Dictionary of available label sizes
        printers_list: List of available printers
        config: Configuration dictionary to validate

    Returns:
        List of error messages (empty if no errors)
    """
    errors = []

    # Check if fonts are available
    if not fonts_dict:
        errors.append("No fonts found on the system. Please install fonts to the system or configure additional font folder.")

    # Check printer availability/configuration
    configured_printer = config.get('PRINTER', {}).get('PRINTER')
    # If we have printers from CUPS/config
    if not printers_list:
        errors.append("No printers detected. Please ensure CUPS is available and printers are configured.")
    else:
        # Accept missing configured printer when CUPS provides a default
        if configured_printer:
            if configured_printer not in printers_list:
                errors.append(f"Configured default printer '{configured_printer}' not found among available printers.")
        # else: no configured printer is fine if printers exist (CUPS default or selection can be used)

    # Check that label sizes are available
    if not label_sizes_dict:
        errors.append("No label sizes available. Ensure CUPS server has configured media or enter custom sizes in the configuration.")

    # Check default font configuration
    default_fonts_list = config.get('LABEL', {}).get('DEFAULT_FONTS', [])
    if isinstance(default_fonts_list, dict):
        default_fonts_list = [default_fonts_list]

    for font in default_fonts_list:
        family = font.get('family')
        style = font.get('style')
        if family and style:
            if family not in fonts_dict:
                errors.append(f"Configured default font family '{family}' not found in system fonts.")
            elif style not in fonts_dict.get(family, {}):
                errors.append(f"Configured default font style '{style}' not found for font family '{family}'.")

    # Check default label size configuration
    default_size = config.get('LABEL', {}).get('DEFAULT_SIZE')
    if default_size and label_sizes_dict:
        if default_size not in label_sizes_dict.keys():
            errors.append(f"Configured default label size '{default_size}' is not in available label sizes.")

    return errors


def compute_printer_selection(instance, printers, config, logger=None):
    """Compute filtered printers, default printer, and label sizes for UI templates."""
    filtered_printers = filter_printers(printers or [], config)
    default_printer = None
    if instance.selected_printer and instance.selected_printer in filtered_printers:
        default_printer = instance.selected_printer
    elif filtered_printers:
        default_printer = filtered_printers[0]

    label_sizes_list = instance.get_label_sizes(default_printer)
    label_sizes_list = filter_label_sizes_for_printer(label_sizes_list, default_printer, config)
    label_sizes = label_sizes_list_to_dict(label_sizes_list, logger)
    return filtered_printers, default_printer, label_sizes
