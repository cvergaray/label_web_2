import unittest
from unittest.mock import patch

import brother_ql_web


class TestPreviewDpi(unittest.TestCase):
    def test_get_effective_printer_dpi_uses_instance_lookup(self):
        """The preview DPI should come from implementation printer DPI lookup when available."""
        with patch.object(brother_ql_web.instance, '_get_printer_dpi', return_value=600, create=True):
            self.assertEqual(brother_ql_web.get_effective_printer_dpi('printer-a'), 600)

    def test_get_effective_printer_dpi_falls_back_to_default_config_dpi(self):
        """If printer DPI lookup fails, use configured DEFAULT_DPI."""
        test_config = {
            'PRINTER': {
                'DEFAULT_DPI': 300,
            }
        }

        with patch.object(brother_ql_web, 'CONFIG', test_config), \
             patch.object(brother_ql_web.instance, '_get_printer_dpi', side_effect=RuntimeError('lookup failed'), create=True):
            self.assertEqual(brother_ql_web.get_effective_printer_dpi('printer-a'), 300)

    def test_get_effective_printer_dpi_falls_back_to_203_when_no_other_dpi_available(self):
        """Use legacy thermal-printer default as a last resort."""
        with patch.object(brother_ql_web, 'CONFIG', {'PRINTER': {}}), \
             patch.object(brother_ql_web.instance, '_get_printer_dpi', side_effect=RuntimeError('lookup failed'), create=True):
            self.assertEqual(brother_ql_web.get_effective_printer_dpi('printer-a'), 203)


if __name__ == '__main__':
    unittest.main()


