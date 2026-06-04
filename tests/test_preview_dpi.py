from unittest.mock import patch

import brother_ql_web


def test_get_effective_printer_dpi_uses_instance_lookup():
    """The preview DPI should come from the implementation's printer DPI lookup when available."""
    with patch.object(brother_ql_web.instance, '_get_printer_dpi', return_value=600, create=True):
        assert brother_ql_web.get_effective_printer_dpi('printer-a') == 600


def test_get_effective_printer_dpi_falls_back_to_default_config_dpi():
    """If printer DPI lookup fails, the configured DEFAULT_DPI should be used."""
    test_config = {
        'PRINTER': {
            'DEFAULT_DPI': 300,
        }
    }

    with patch.object(brother_ql_web, 'CONFIG', test_config), \
         patch.object(brother_ql_web.instance, '_get_printer_dpi', side_effect=RuntimeError('lookup failed'), create=True):
        assert brother_ql_web.get_effective_printer_dpi('printer-a') == 300


def test_get_effective_printer_dpi_falls_back_to_203_when_no_other_dpi_available():
    """The legacy thermal-printer default should be used as a last resort."""
    with patch.object(brother_ql_web, 'CONFIG', {'PRINTER': {}}), \
         patch.object(brother_ql_web.instance, '_get_printer_dpi', side_effect=RuntimeError('lookup failed'), create=True):
        assert brother_ql_web.get_effective_printer_dpi('printer-a') == 203

