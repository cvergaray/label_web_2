# NOTE: Requires the 'pycups' library. Install with: pip install pycups
import cups
import re
from constants import PARSEABLE_SIZE_PATTERN

# Conversion constants
POINTS_PER_INCH = 72.0  # PostScript/CUPS points per inch

# Printer-specific settings
# Set these based on your printer and loaded labels

# A dictionary of an identifier of the loaded label sizes to a human-readable description of the label size
#label_sizes = [
#               ('2.25x1.25', '2.25" by 1.25"'),
#               ('1.25x2.25', '1.25" x 2.25"')
#              ]

# A mapping of the keys from label_sizes to the size of that label in DPI.
# This can be calculated by multiplying one dimension by the printer resolution
#label_printable_area = {
#                '2.25x1.25': (457, 254),
#                '1.25x2.25': (254, 457)
#                }

# The default size of a label. This must be one of the keys in the label_sizes dictionary.
#default_size = '2.25x1.25'

# The name of the printer as exposed by CUPS.
#printer_name = 'UPS-Thermal-2844'

#server_ip = '192.168.1.176'

# End of Printer Specific Settings

class implementation:

    def __init__(self):
        #Common Properties
        self.DEBUG = False
        self.CONFIG = None
        self.logger = None
        self.server_ip = None
        self.selected_printer = None
        self.initialization_errors = []  # Track initialization and CUPS errors
        self.cups_default = None  # Track CUPS-reported default printer

    def initialize(self, config):
        self.CONFIG = config
        self.initialization_errors = []  # Clear any previous errors
        self.cups_default = None
        self.server_ip = None

        # Ensure PRINTER section exists and is a dict
        if 'PRINTER' not in self.CONFIG or self.CONFIG['PRINTER'] is None:
            self.CONFIG['PRINTER'] = {}
            error_msg = "No printer configuration found in config file. Using defaults."
            self.initialization_errors.append(error_msg)

        if 'SERVER' in self.CONFIG['PRINTER']:
            self.server_ip = self.CONFIG['PRINTER']['SERVER']

        cups.setServer(self.server_ip)

        # Test CUPS connection
        try:
            # Try to connect to verify the server is accessible
            conn = self._get_conn()
            # Verify we can get printers to ensure full connectivity
            _ = conn.getPrinters()
            self.cups_default = conn.getDefault() or None
        except Exception as e:
            error_msg = f"Failed to retrieve printer data from CUPS server at '{self.server_ip or 'localhost'}': {str(e)}"
            self.cups_default = None
            self.initialization_errors.append(error_msg)
            print(f"Error: {error_msg}")

        # Optionally set default printer from config or CUPS default
        configured_printer = self.CONFIG['PRINTER'].get('PRINTER')
        self.selected_printer = configured_printer or self.cups_default
        return ''

    def _get_conn(self):
        return cups.Connection()

    def _get_printer_name(self, printerName=None):
        if printerName:
            return printerName
        if self.selected_printer:
            return self.selected_printer
        try:
            return self._get_conn().getDefault()
        except Exception:
            return None

    def _should_use_cups(self):
        """Check if CUPS should be used based on configuration flag. Defaults to False."""
        return self.CONFIG.get('PRINTER', {}).get('USE_CUPS', False)

    def _parse_media_name(self, media_name):
        # CUPS media names are often like 'na_index-4x6_4x6in' or 'iso_a4_210x297mm'
        # We'll try to extract the size part for short name, and a readable long name
        import re
        match = re.search(r'(\d+(?:\.\d+)?)[xX](\d+(?:\.\d+)?)(in|mm)', media_name)
        if match:
            w, h, unit = match.groups()
            short = f"{w}x{h}{unit}"
            long = f"{w}{unit} x {h}{unit}"
            return short, long
        return media_name, media_name

    def _get_printer_dpi(self, printerName=None):
        """Get the DPI/resolution of the printer, with fallback to 203 DPI"""
        try:
            printerName = self._get_printer_name(printerName)
            conn = self._get_conn()
            attrs = conn.getPrinterAttributes(printerName, requested_attributes=["printer-resolution-default"])
            resolution = attrs.get("printer-resolution-default")
            if resolution:
                # Resolution is typically (xdpi, ydpi, units) where units is 3 for DPI
                if isinstance(resolution, tuple) and len(resolution) >= 2:
                    return resolution[0]  # Return X DPI
        except:
            pass
        return 203  # Default DPI for thermal label printers

    def _convert_to_cups_media_format(self, label_size, printerName=None, dpi=None):
        """
        Convert a custom label size to CUPS-compatible media format.

        Valid CUPS custom formats:
          Custom.WIDTHxLENGTH      - measured in points (1/72 inch)
          Custom.WIDTHxLENGTHin    - measured in inches
          Custom.WIDTHxLENGTHcm    - measured in centimeters
          Custom.WIDTHxLENGTHmm    - measured in millimeters
          Custom.WIDTHxLENGTHpt    - measured in points (explicit)

        Args:
            label_size: Size key, may be in format "4x6in", "Custom.4x6in", etc.
            printerName: Optional printer name for DPI lookup
            dpi: Optional explicit DPI value

        Returns the CUPS-compatible media name with "Custom." prefix, or the original if conversion fails.
        """

        # Check if already in valid CUPS custom format (Custom.WxHunit)
        if label_size.startswith('Custom.'):
            # Validate the format after "Custom."
            size_part = label_size[7:]  # Remove "Custom." prefix
            match = re.search(PARSEABLE_SIZE_PATTERN, size_part, re.IGNORECASE)
            if match:
                # Already in valid format, return as-is
                return label_size
            # Invalid format after Custom., try to parse without prefix
            label_size = size_part

        # Try to parse the size using the standard pattern
        match = re.search(PARSEABLE_SIZE_PATTERN, label_size, re.IGNORECASE)
        if match:
            w, h, unit = match.groups()
            # If unit is provided, construct the CUPS format with that unit
            if unit:
                unit_lower = unit.lower()
                return f"Custom.{w}x{h}{unit_lower}"
            # No unit provided - check if dimensions are in config (pixel-based)
            # Otherwise default to points
            pass  # Fall through to config lookup

        # Try to get dimensions from config
        if 'PRINTER' not in self.CONFIG or 'LABEL_PRINTABLE_AREA' not in self.CONFIG['PRINTER']:
            # No config available, if we have a parseable name without unit, assume points
            if match and not match.groups()[2]:
                w, h, _ = match.groups()
                return f"Custom.{w}x{h}"  # No unit = points in CUPS
            return label_size

        if label_size not in self.CONFIG['PRINTER']['LABEL_PRINTABLE_AREA']:
            # Not in config, if we have a parseable name without unit, assume points
            if match and not match.groups()[2]:
                w, h, _ = match.groups()
                return f"Custom.{w}x{h}"  # No unit = points in CUPS
            return label_size

        # Get pixel dimensions from config
        width_px, height_px = self.CONFIG['PRINTER']['LABEL_PRINTABLE_AREA'][label_size]

        # Get printer DPI
        if dpi is None:
            dpi = self._get_printer_dpi(printerName)

        # Convert pixels to millimeters
        width_mm = (width_px / dpi) * 25.4
        height_mm = (height_px / dpi) * 25.4

        # Format as CUPS custom media name (use integer mm values for compatibility)
        cups_media_name = f"Custom.{int(round(width_mm))}x{int(round(height_mm))}mm"

        return cups_media_name

    def _media_name_to_dimensions(self, media_name, printerName=None):
        """
        Get media dimensions in pixels.
        Priority: 1) CUPS media-size-supported, 2) Parse from name, 3) Return None
        """
        printerName = self._get_printer_name(printerName)

        # Try to get dimensions from CUPS media-size-supported (only if CUPS enabled)
        if self._should_use_cups():
            try:
                conn = self._get_conn()
                attrs = conn.getPrinterAttributes(printerName,
                    requested_attributes=["media-size-supported", "media-supported"])

                media_supported = attrs.get("media-supported", [])
                media_sizes = attrs.get("media-size-supported", [])

                # Find the index of our media in the supported list
                if media_name in media_supported and media_sizes:
                    try:
                        media_index = media_supported.index(media_name)
                        if media_index < len(media_sizes):
                            # media-size-supported is a list of dicts with x-dimension and y-dimension
                            # Each dimension is in hundredths of millimeters
                            size_info = media_sizes[media_index]
                            if isinstance(size_info, dict):
                                x_dim = size_info.get('x-dimension', 0)
                                y_dim = size_info.get('y-dimension', 0)

                                if x_dim and y_dim:
                                    # Convert from hundredths of mm to inches to pixels
                                    dpi = self._get_printer_dpi(printerName)
                                    width_in = (x_dim / 100.0) / 25.4
                                    height_in = (y_dim / 100.0) / 25.4
                                    return int(width_in * dpi), int(height_in * dpi)
                    except (ValueError, IndexError, KeyError, TypeError):
                        pass
            except Exception:
                pass

        # Fallback: Try to extract dimensions from media name
        import re
        match = re.search(r'(\d+(?:\.\d+)?)[xX](\d+(?:\.\d+)?)(in|mm)', media_name)
        if match:
            w, h, unit = match.groups()
            w = float(w)
            h = float(h)
            dpi = self._get_printer_dpi(printerName)

            if not unit or unit.lower() == 'pt':
                # Points (1/72 inch) - CUPS default when no unit specified
                w_in = w / POINTS_PER_INCH
                h_in = h / POINTS_PER_INCH
                return int(w_in * dpi), int(h_in * dpi)
            elif unit.lower() == 'in':
                # Convert inches to pixels using printer DPI
                return int(w * dpi), int(h * dpi)
            elif unit.lower() == 'mm':
                # Convert mm to inches, then to pixels
                w_in = w / 25.4
                h_in = h / 25.4
                return int(w_in * dpi), int(h_in * dpi)
            elif unit.lower() == 'cm':
                # Convert cm to inches, then to pixels
                w_in = w / 2.54
                h_in = h / 2.54
                return int(w_in * dpi), int(h_in * dpi)

        return None

    # Provides an array of label sizes. Each entry in the array is a tuple of ('full_cups_name', 'long_display_name')
    # For CUPS: full name is used as key (e.g., 'na_index-4x6_4x6in'), long name for display (e.g., '4in x 6in')
    # For config: uses config keys as-is for both key and display
    # When CUPS is enabled, this merges CUPS media (including custom CUPS sizes) with config custom sizes

    def get_label_sizes(self, printer_name=None):
        # Check if CUPS should be used
        if not self._should_use_cups():
            # Use config only
            config_sizes = self.CONFIG.get('PRINTER', {}).get('LABEL_SIZES', {})
            if isinstance(config_sizes, dict):
                return [(key, value) for key, value in config_sizes.items()]
            elif isinstance(config_sizes, list):
                return config_sizes
            return []

        # CUPS is enabled, query it and merge with custom sizes from config
        printer_name = self._get_printer_name(printer_name)
        cups_sizes = []

        # Only attempt CUPS query if we have a valid printer name
        if printer_name:
            try:
                conn = self._get_conn()
                # Get all supported media from CUPS (includes standard and custom CUPS sizes)
                attrs = conn.getPrinterAttributes(printer_name, requested_attributes=["media-supported"])
                media_supported = attrs.get("media-supported", [])

                for media in media_supported:
                    # Ensure media is a string (it might be bytes in some cases)
                    if isinstance(media, bytes):
                        media = media.decode('utf-8')
                    elif not isinstance(media, str):
                        media = str(media)

                    short, long = self._parse_media_name(media)
                    # Use full CUPS media name as key, long name as display value
                    cups_sizes.append((media, long))
            except Exception as e:
                print(f"Warning: Could not retrieve CUPS media sizes: {e}")

        # Get custom sizes from config
        config_sizes = self.CONFIG.get('PRINTER', {}).get('LABEL_SIZES', {})
        custom_sizes = []

        dpi = self._get_printer_dpi(printer_name)

        if isinstance(config_sizes, dict):
            custom_sizes = [(self._convert_to_cups_media_format(key, printer_name, dpi), value) for key, value in config_sizes.items()]
        elif isinstance(config_sizes, list):
            custom_sizes = [(self._convert_to_cups_media_format(size[0], printer_name, dpi), size[1]) for size in config_sizes]

        # Merge CUPS sizes with custom config sizes, avoiding duplicates
        # CUPS sizes take precedence - only add config sizes if key doesn't exist in CUPS
        cups_keys = {size[0] for size in cups_sizes}
        merged_sizes = cups_sizes.copy()

        for custom_size in custom_sizes:
            if custom_size[0] not in cups_keys:
                merged_sizes.append(custom_size)

        # Return merged list, or config-only if CUPS query failed and returned nothing
        return merged_sizes if merged_sizes else custom_sizes


    def get_default_label_size(self, printerName=None):
        # Check if CUPS should be used
        if not self._should_use_cups():
            # Use config only
            return self.CONFIG.get('LABEL', {}).get('DEFAULT_SIZE')

        # CUPS is enabled, try to query it
        printerName = self._get_printer_name(printerName)
        try:
            conn = self._get_conn()
            attrs = conn.getPrinterAttributes(printerName, requested_attributes=["media-default"])
            media_default = attrs.get("media-default")
            if media_default:
                # Return the full CUPS media name as the key
                return media_default
        except Exception:
            pass
        return self.CONFIG['LABEL'].get('DEFAULT_SIZE')

    def get_label_kind(self, label_size_description, printerName=None):
        # For CUPS, the label kind is typically the media name
        return label_size_description


    def get_printer_properties(self, printerName=None):
        printerName = self._get_printer_name(printerName)
        conn = self._get_conn()
        return conn.getPrinterAttributes(printerName, requested_attributes=["media-default", "media-supported", "printer-resolution-supported", "printer-resolution-default"])

    def get_label_dimensions(self, label_size, printerName=None):
        """
        Get label dimensions in pixels for a given media.
        Priority: 1) CUPS media dimensions, 2) Parse from name, 3) Config fallback, 4) Default size
        """
        printerName = self._get_printer_name(printerName)

        # Helper function to get dimensions from config
        def get_from_config():
            if 'PRINTER' in self.CONFIG and 'LABEL_PRINTABLE_AREA' in self.CONFIG['PRINTER']:
                if label_size in self.CONFIG['PRINTER']['LABEL_PRINTABLE_AREA']:
                    printable_area = self.CONFIG['PRINTER']['LABEL_PRINTABLE_AREA'][label_size]
                    print(f"Info: Using dimensions from config for '{label_size}': {printable_area}")

                    return tuple(printable_area)
            return None

        try:
            # Try to get dimensions from CUPS (includes both direct query and name parsing)
            dims = self._media_name_to_dimensions(label_size, printerName)
            if dims:
                print(f"Info: Using dimensions from CUPS for '{label_size}': {dims}")
                return dims

            # If CUPS method didn't work, try config fallback
            dims = get_from_config()
            if dims:
                return dims

            # If not found anywhere, return a default size
            print(f"Warning: No dimensions found for '{label_size}', using default (300, 200)")
            return (300, 200)

        except Exception as e:
            # On any exception, try config fallback
            print(f"Warning: Exception getting dimensions for '{label_size}': {e}")
            dims = get_from_config()
            if dims:
                return dims

            # Return a default size as last resort
            print(f"Warning: Using default dimensions (300, 200) for '{label_size}'")
            return (300, 200)

    def get_label_width_height(self, textsize, **kwargs):
        # Returns the width and height for the label, based on kwargs or textsize fallback
        width = kwargs.get('width')
        height = kwargs.get('height')
        if width is not None and height is not None:
            return width, height
        if textsize:
            return textsize[0], textsize[1]
        return 0, 0

    def get_label_offset(self, calculated_width, calculated_height, textsize, **kwargs):
        # Returns the offset for the label, based on orientation and margins
        orientation = kwargs.get('orientation', 'standard')
        margin_top = kwargs.get('margin_top', 0)
        margin_bottom = kwargs.get('margin_bottom', 0)
        margin_left = kwargs.get('margin_left', 0)
        horizontal_offset = 0
        vertical_offset = 0
        if orientation == 'standard':
            vertical_offset = margin_top
            horizontal_offset = max((calculated_width - textsize[0])//2, 0) if textsize else 0
        elif orientation == 'rotated':
            vertical_offset  = (calculated_height - textsize[1])//2 if textsize else 0
            vertical_offset += (margin_top - margin_bottom)//2
            horizontal_offset = margin_left
        offset = horizontal_offset, vertical_offset
        return offset

    def get_printers(self):
        # Check if CUPS should be used
        if not self._should_use_cups():
            # Use config only - return configured printer if available
            printer = self.CONFIG.get('PRINTER', {}).get('PRINTER')
            if printer:
                return [printer]
            return []

        # CUPS is enabled, try to query it
        try:
            conn = self._get_conn()
            printers = list(conn.getPrinters().keys())
        except Exception as e:
            error_msg = f"Error getting list of printers from CUPS server: {str(e)}"
            print(error_msg)
            # Add to initialization errors if not already there
            if error_msg not in self.initialization_errors:
                self.initialization_errors.append(error_msg)
            printers = []
        return printers

    def print_label(self, im, **context):
        return_dict = {'success': False, 'message': ''}
        try:
            print(context)
            im.save('sample-out.png')
            quantity = context.get("quantity", 1)
            conn = self._get_conn()
            printer_name = context.get("printer")
            if printer_name is None:
                print("No printer specified in Context")
                printer_name = self.CONFIG['PRINTER'].get("PRINTER")
            if printer_name is None:
                print("No printer specified in Config")
                printer_name = str(conn.getDefault())

            # Build print options with copies and media size
            options = {"copies": str(quantity)}

            # Add media size to options if specified in context
            label_size = context.get("label_size")
            if label_size:
                should_add_media = False
                cups_media_name = label_size  # Default to the original label size

                if self._should_use_cups():
                    # Verify the selected media is available on this printer (only if CUPS enabled)
                    try:
                        attrs = conn.getPrinterAttributes(printer_name, requested_attributes=["media-supported"])
                        media_supported = attrs.get("media-supported", [])

                        # Check if the selected media is in the CUPS supported list
                        if label_size in media_supported:
                            # Media is available in CUPS, pass it as-is
                            should_add_media = True
                        else:
                            # Check if it's a custom size from config
                            config_sizes = self.CONFIG.get('PRINTER', {}).get('LABEL_SIZES', {})
                            if isinstance(config_sizes, dict) and label_size in config_sizes:
                                # It's a custom config size, convert it to CUPS format
                                cups_media_name = self._convert_to_cups_media_format(label_size, printer_name)
                                should_add_media = True
                                print(f"Info: Using custom config size '{label_size}' (converted to '{cups_media_name}') for printer '{printer_name}'.")
                            elif isinstance(config_sizes, list) and any(size[0] == label_size for size in config_sizes):
                                # It's in the config list format, convert it
                                cups_media_name = self._convert_to_cups_media_format(label_size, printer_name)
                                should_add_media = True
                                print(f"Info: Using custom config size '{label_size}' (converted to '{cups_media_name}') for printer '{printer_name}'.")
                            else:
                                print(f"Warning: Selected media '{label_size}' not available on printer '{printer_name}'. Attempting to use selected size anyway.")
                                should_add_media = True
                    except Exception as e:
                        print(f"Warning: Could not verify media availability: {e}. Attempting to use selected size anyway.")
                        should_add_media = True
                else:
                    # CUPS is disabled, pass media size directly without verification
                    should_add_media = True

                if should_add_media:
                    options["media"] = cups_media_name

            print(printer_name, options)
            conn.printFile(printer_name, 'sample-out.png', "grocy", options)

            return_dict['success'] = True
        except Exception as e:
            return_dict['success'] = False
            return_dict['message'] = str(e)
        return return_dict