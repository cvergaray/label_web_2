"""
Test suite for DPI configuration features.

Tests cover:
- Per-printer DPI configuration
- DEFAULT_DPI global fallback
- Configuration format conversions
- DPI priority ordering
- CUPS unit conversion
"""
import unittest
from unittest.mock import MagicMock, patch
import sys

# Mock the cups module before importing implementation_cups
sys.modules['cups'] = MagicMock()

import configuration_management as cm
from implementation_cups import implementation


class TestDpiConfigurationConversion(unittest.TestCase):
    """Test DPI configuration conversion between formats"""

    def test_config_to_settings_includes_dpi(self):
        """Test that config_to_settings_format includes DPI"""
        config = {
            'SERVER': {'HOST': '', 'LOGLEVEL': 'INFO'},
            'PRINTER': {
                'USE_CUPS': False,
                'SERVER': 'localhost',
                'PRINTER': 'test-printer',
                'DPI': {
                    'printer1': 203,
                    'printer2': 300
                }
            },
            'LABEL': {'DEFAULT_SIZE': '62'},
            'WEBSITE': {}
        }

        settings = cm.config_to_settings_format(config)
        self.assertIn('dpi', settings['printer'], "DPI not found in settings printer section")
        self.assertEqual(settings['printer']['dpi'], {'printer1': 203, 'printer2': 300})

    def test_settings_to_config_includes_dpi(self):
        """Test that settings_format_to_config includes DPI"""
        settings = {
            'server': {'host': '', 'logLevel': 'INFO'},
            'printer': {
                'useCups': False,
                'server': 'localhost',
                'printer': 'test-printer',
                'dpi': {
                    'printer-a': 203,
                    'printer-b': 600
                }
            },
            'label': {'defaultSize': '62'},
            'website': {}
        }

        config_result = cm.settings_format_to_config(settings)
        self.assertIn('DPI', config_result['PRINTER'], "DPI not found in config PRINTER section")
        self.assertEqual(config_result['PRINTER']['DPI'], {'printer-a': 203, 'printer-b': 600})

    def test_dpi_roundtrip_conversion(self):
        """Test that DPI is preserved through round-trip conversion"""
        original_config = {
            'SERVER': {},
            'PRINTER': {
                'DPI': {'zebra': 203, 'dymo': 300}
            },
            'LABEL': {},
            'WEBSITE': {}
        }

        settings = cm.config_to_settings_format(original_config)
        final_config = cm.settings_format_to_config(settings)

        self.assertEqual(final_config['PRINTER']['DPI'], {'zebra': 203, 'dymo': 300})

    def test_empty_dpi_handled_correctly(self):
        """Test that empty DPI dictionary is handled correctly"""
        config_no_dpi = {
            'SERVER': {},
            'PRINTER': {},
            'LABEL': {},
            'WEBSITE': {}
        }

        settings = cm.config_to_settings_format(config_no_dpi)
        self.assertIn('dpi', settings['printer'], "DPI key should exist even if empty")
        self.assertEqual(settings['printer']['dpi'], {})


class TestDefaultDpiConfiguration(unittest.TestCase):
    """Test DEFAULT_DPI configuration handling"""

    def test_config_to_settings_includes_default_dpi(self):
        """Test that config_to_settings_format includes defaultDpi"""
        config = {
            'SERVER': {'HOST': '', 'LOGLEVEL': 'INFO'},
            'PRINTER': {
                'USE_CUPS': False,
                'SERVER': 'localhost',
                'PRINTER': 'test-printer',
                'DEFAULT_DPI': 300,
                'DPI': {
                    'printer1': 203
                }
            },
            'LABEL': {'DEFAULT_SIZE': '62'},
            'WEBSITE': {}
        }

        settings = cm.config_to_settings_format(config)
        self.assertIn('defaultDpi', settings['printer'])
        self.assertEqual(settings['printer']['defaultDpi'], 300)

    def test_settings_to_config_includes_default_dpi(self):
        """Test that settings_format_to_config includes DEFAULT_DPI"""
        settings = {
            'server': {'host': '', 'logLevel': 'INFO'},
            'printer': {
                'useCups': False,
                'server': 'localhost',
                'printer': 'test-printer',
                'defaultDpi': 600,
                'dpi': {'printer-a': 203}
            },
            'label': {'defaultSize': '62'},
            'website': {}
        }

        config_result = cm.settings_format_to_config(settings)
        self.assertIn('DEFAULT_DPI', config_result['PRINTER'])
        self.assertEqual(config_result['PRINTER']['DEFAULT_DPI'], 600)

    def test_default_dpi_defaults_to_203(self):
        """Test that defaultDpi defaults to 203 when not specified"""
        config_no_default = {
            'SERVER': {},
            'PRINTER': {},
            'LABEL': {},
            'WEBSITE': {}
        }

        settings = cm.config_to_settings_format(config_no_default)
        self.assertEqual(settings['printer']['defaultDpi'], 203)


class TestPerPrinterDpiRetrieval(unittest.TestCase):
    """Test per-printer DPI retrieval from configuration"""

    def test_per_printer_dpi_from_config(self):
        """Test that per-printer DPI is retrieved from config"""
        impl = implementation()
        impl.CONFIG = {
            'PRINTER': {
                'DPI': {
                    'printer1': 300,
                    'printer2': 600
                },
                'PRINTER': 'printer1'
            }
        }
        impl.selected_printer = 'printer1'

        dpi1 = impl._get_printer_dpi('printer1')
        self.assertEqual(dpi1, 300)

        dpi2 = impl._get_printer_dpi('printer2')
        self.assertEqual(dpi2, 600)

    def test_fallback_to_default_when_not_in_config(self):
        """Test fallback to default DPI when printer not in config"""
        impl = implementation()
        impl.CONFIG = {
            'PRINTER': {
                'DPI': {
                    'printer1': 300
                },
                'PRINTER': 'printer1'
            }
        }
        impl.selected_printer = 'printer1'

        dpi = impl._get_printer_dpi('printer3')
        self.assertEqual(dpi, 203)

    def test_fallback_when_no_dpi_section(self):
        """Test fallback when no DPI section in config"""
        impl = implementation()
        impl.CONFIG = {'PRINTER': {'PRINTER': 'printer1'}}

        dpi = impl._get_printer_dpi('printer1')
        self.assertEqual(dpi, 203)


class TestCupsUnitConversion(unittest.TestCase):
    """Test CUPS resolution unit conversion"""

    def test_cups_unit_3_dpi_no_conversion(self):
        """Test that CUPS unit 3 (DPI) requires no conversion"""
        impl = implementation()
        impl.CONFIG = {'PRINTER': {}}
        impl.selected_printer = 'test-printer'

        with patch.object(impl, '_get_conn') as mock_conn:
            mock_attrs = {'printer-resolution-default': (203, 203, 3)}
            mock_conn.return_value.getPrinterAttributes.return_value = mock_attrs

            dpi = impl._get_printer_dpi('test-printer')
            self.assertEqual(dpi, 203)

    def test_cups_unit_4_dpcm_conversion(self):
        """Test that CUPS unit 4 (DPCM) is converted to DPI"""
        impl = implementation()
        impl.CONFIG = {'PRINTER': {}}
        impl.selected_printer = 'test-printer'

        with patch.object(impl, '_get_conn') as mock_conn:
            # 80 DPCM = 203.2 DPI (80 * 2.54)
            mock_attrs = {'printer-resolution-default': (80, 80, 4)}
            mock_conn.return_value.getPrinterAttributes.return_value = mock_attrs

            dpi = impl._get_printer_dpi('test-printer')
            self.assertEqual(dpi, 203)

    def test_cups_unknown_unit_assumes_dpi(self):
        """Test that unknown CUPS units are assumed to be DPI"""
        impl = implementation()
        impl.CONFIG = {'PRINTER': {}}
        impl.selected_printer = 'test-printer'

        with patch.object(impl, '_get_conn') as mock_conn:
            mock_attrs = {'printer-resolution-default': (300, 300, 99)}
            mock_conn.return_value.getPrinterAttributes.return_value = mock_attrs

            dpi = impl._get_printer_dpi('test-printer')
            self.assertEqual(dpi, 300)


class TestDpiPriorityOrder(unittest.TestCase):
    """Test DPI priority ordering (per-printer > CUPS > DEFAULT_DPI > hard-coded)"""

    def test_per_printer_overrides_default_dpi(self):
        """Test that per-printer DPI overrides DEFAULT_DPI"""
        impl = implementation()
        impl.CONFIG = {
            'PRINTER': {
                'DEFAULT_DPI': 300,
                'DPI': {
                    'printer1': 203
                },
                'PRINTER': 'printer1'
            }
        }
        impl.selected_printer = 'printer1'

        dpi = impl._get_printer_dpi('printer1')
        self.assertEqual(dpi, 203)

    def test_default_dpi_used_when_per_printer_not_configured(self):
        """Test that DEFAULT_DPI is used when per-printer not configured"""
        impl = implementation()
        impl.CONFIG = {
            'PRINTER': {
                'DEFAULT_DPI': 300,
                'DPI': {
                    'printer1': 203
                },
                'PRINTER': 'printer1'
            }
        }
        impl.selected_printer = 'printer1'

        dpi = impl._get_printer_dpi('printer2')
        self.assertEqual(dpi, 300)

    def test_hard_coded_used_when_default_dpi_not_set(self):
        """Test that hard-coded 203 is used when DEFAULT_DPI not set"""
        impl = implementation()
        impl.CONFIG = {'PRINTER': {'PRINTER': 'printer1'}}

        dpi = impl._get_printer_dpi('printer1')
        self.assertEqual(dpi, 203)

    def test_default_dpi_zero_falls_back_to_hard_coded(self):
        """Test that DEFAULT_DPI=0 falls back to hard-coded 203"""
        impl = implementation()
        impl.CONFIG = {
            'PRINTER': {
                'DEFAULT_DPI': 0,
                'PRINTER': 'printer1'
            }
        }

        dpi = impl._get_printer_dpi('printer1')
        self.assertEqual(dpi, 203)

    def test_per_printer_overrides_cups(self):
        """Test that per-printer DPI overrides CUPS value"""
        impl = implementation()
        impl.CONFIG = {
            'PRINTER': {
                'DEFAULT_DPI': 300,
                'DPI': {
                    'printer1': 203
                }
            }
        }

        with patch.object(impl, '_get_conn') as mock_conn:
            mock_attrs = {'printer-resolution-default': (600, 600, 3)}
            mock_conn.return_value.getPrinterAttributes.return_value = mock_attrs

            dpi = impl._get_printer_dpi('printer1')
            self.assertEqual(dpi, 203)

    def test_cups_overrides_default_dpi(self):
        """Test that CUPS value overrides DEFAULT_DPI"""
        impl = implementation()
        impl.CONFIG = {
            'PRINTER': {
                'DEFAULT_DPI': 300
            }
        }

        with patch.object(impl, '_get_conn') as mock_conn:
            mock_attrs = {'printer-resolution-default': (600, 600, 3)}
            mock_conn.return_value.getPrinterAttributes.return_value = mock_attrs

            dpi = impl._get_printer_dpi('test-printer')
            self.assertEqual(dpi, 600)

    def test_default_dpi_used_when_cups_fails(self):
        """Test that DEFAULT_DPI is used when CUPS fails"""
        impl = implementation()
        impl.CONFIG = {
            'PRINTER': {
                'DEFAULT_DPI': 300
            }
        }

        with patch.object(impl, '_get_conn') as mock_conn:
            mock_conn.side_effect = Exception("CUPS error")

            dpi = impl._get_printer_dpi('test-printer')
            self.assertEqual(dpi, 300)

    def test_per_printer_highest_priority(self):
        """Test that per-printer DPI has highest priority in complete chain"""
        impl = implementation()
        impl.CONFIG = {
            'PRINTER': {
                'DEFAULT_DPI': 300,
                'DPI': {'test-printer': 999}
            }
        }

        with patch.object(impl, '_get_conn') as mock_conn:
            mock_attrs = {'printer-resolution-default': (600, 600, 3)}
            mock_conn.return_value.getPrinterAttributes.return_value = mock_attrs

            dpi = impl._get_printer_dpi('test-printer')
            self.assertEqual(dpi, 999)


if __name__ == '__main__':
    unittest.main()

