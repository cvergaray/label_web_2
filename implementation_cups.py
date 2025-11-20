# NOTE: Requires the 'pycups' library. Install with: pip install pycups
import cups

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

    def initialize(self, config):
        self.CONFIG = config
        self.server_ip = None
        if 'PRINTER' not in self.CONFIG:
            return "No printer configuration found in config file."
        if 'SERVER' in self.CONFIG['PRINTER']:
            self.server_ip = self.CONFIG['PRINTER']['SERVER']
        cups.setServer(self.server_ip)
        # Optionally set default printer from config
        self.selected_printer = self.CONFIG['PRINTER'].get('PRINTER')
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

    def _media_name_to_dimensions(self, media_name, printerName=None):
        """
        Get media dimensions in pixels.
        Priority: 1) CUPS media-size-supported, 2) Parse from name, 3) Return None
        """
        printerName = self._get_printer_name(printerName)

        # Try to get dimensions from CUPS media-size-supported
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

            if unit == 'in':
                # Convert inches to pixels using printer DPI
                return int(w * dpi), int(h * dpi)
            elif unit == 'mm':
                # Convert mm to inches, then to pixels
                w_in = w / 25.4
                h_in = h / 25.4
                return int(w_in * dpi), int(h_in * dpi)

        return None

    # Provides an array of label sizes. Each entry in the array is a tuple of ('full_cups_name', 'long_display_name')
    # For CUPS: full name is used as key (e.g., 'na_index-4x6_4x6in'), long name for display (e.g., '4in x 6in')
    # For config: uses config keys as-is for both key and display
    def get_label_sizes(self, printer_name=None):
        printer_name = self._get_printer_name(printer_name)
        try:
            conn = self._get_conn()
            attrs = conn.getPrinterAttributes(printer_name, requested_attributes=["media-supported"])
            media_supported = attrs.get("media-supported", [])
            sizes = []
            for media in media_supported:
                short, long = self._parse_media_name(media)
                # Use full CUPS media name as key, long name as display value
                sizes.append((media, long))
            if sizes:
                return sizes
            # If no sizes from CUPS, fall back to config
            raise Exception("No media-supported found")
        except Exception as e:
            # Fallback to config on exception
            config_sizes = self.CONFIG.get('PRINTER', {}).get('LABEL_SIZES', {})
            if isinstance(config_sizes, dict):
                return [(key, value) for key, value in config_sizes.items()]
            elif isinstance(config_sizes, list):
                return config_sizes
            return []

    def get_default_label_size(self, printerName=None):
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

        try:
            # Try to get dimensions from CUPS (includes both direct query and name parsing)
            dims = self._media_name_to_dimensions(label_size, printerName)
            if dims:
                return dims

            # If CUPS method didn't work, try config fallback
            if 'PRINTER' in self.CONFIG and 'LABEL_PRINTABLE_AREA' in self.CONFIG['PRINTER']:
                if label_size in self.CONFIG['PRINTER']['LABEL_PRINTABLE_AREA']:
                    ls = self.CONFIG['PRINTER']['LABEL_PRINTABLE_AREA'][label_size]
                    return tuple(ls)

            # If not found anywhere, return a default size
            return (300, 200)

        except Exception as e:
            # On any exception, try config fallback
            try:
                if 'PRINTER' in self.CONFIG and 'LABEL_PRINTABLE_AREA' in self.CONFIG['PRINTER']:
                    if label_size in self.CONFIG['PRINTER']['LABEL_PRINTABLE_AREA']:
                        ls = self.CONFIG['PRINTER']['LABEL_PRINTABLE_AREA'][label_size]
                        return tuple(ls)
            except:
                pass
            # Return a default size as last resort
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
        try:
            conn = self._get_conn()
            printers = list(conn.getPrinters().keys())
        except Exception as e:
            print("Error getting list of printers. Verify that CUPS server is running and accessible.")
            print(str(e))
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
                # Verify the selected media is available on this printer
                try:
                    attrs = conn.getPrinterAttributes(printer_name, requested_attributes=["media-supported"])
                    media_supported = attrs.get("media-supported", [])

                    # Check if the selected media is in the supported list
                    if label_size in media_supported:
                        # Media is available, pass it as-is (already the full CUPS name)
                        options["media"] = label_size
                    else:
                        print(f"Warning: Selected media '{label_size}' not available on printer '{printer_name}'. Using printer default.")
                except Exception as e:
                    print(f"Warning: Could not verify media availability: {e}. Using printer default.")

            print(printer_name, options)
            conn.printFile(printer_name, 'sample-out.png', "grocy", options)

            return_dict['success'] = True
        except Exception as e:
            return_dict['success'] = False
            return_dict['message'] = str(e)
        return return_dict