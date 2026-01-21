import unittest
from unittest.mock import patch

import brother_ql_web
from implementation_cups import implementation


class FakeConn:
    def __init__(self, printers=None, default=None):
        self._printers = printers or {"cups-default": {}}
        self._default = default or "cups-default"

    def getPrinters(self):
        return self._printers

    def getDefault(self):
        return self._default

    # Minimal stubs for other calls used in code paths
    def printFile(self, *args, **kwargs):
        return None

    def getPrinterAttributes(self, *args, **kwargs):
        return {"media-default": None, "media-supported": [], "printer-resolution-default": None}


class TestPrinterDefaults(unittest.TestCase):
    def test_initialize_uses_cups_default_when_config_missing(self):
        cfg = {
            "PRINTER": {"USE_CUPS": True, "SERVER": "localhost", "PRINTER": ""},
            "LABEL": {"DEFAULT_SIZE": "62", "DEFAULT_ORIENTATION": "standard", "DEFAULT_FONTS": []},
        }

        with patch("implementation_cups.cups.Connection", return_value=FakeConn()) as _conn, \
             patch("implementation_cups.cups.setServer", create=True):
            impl = implementation()
            impl.initialize(cfg)

        self.assertEqual(impl.selected_printer, "cups-default")
        self.assertEqual(impl.initialization_errors, [])

    def test_validate_allows_missing_configured_printer_when_printers_exist(self):
        # Fonts and label sizes provided to avoid unrelated errors
        fonts = {"DejaVu Sans": {"Book": "path"}}
        sizes = {"62": "Label"}
        printers = ["cups-default"]
        cfg = {
            "PRINTER": {"PRINTER": ""},
            "LABEL": {"DEFAULT_FONTS": [], "DEFAULT_SIZE": "62"},
        }

        errors = brother_ql_web.validate_configuration(fonts, sizes, printers, cfg)
        self.assertEqual(errors, [])

    def test_validate_flags_missing_configured_printer_when_printers_exist(self):
        # Fonts and label sizes provided to avoid unrelated errors
        fonts = {"DejaVu Sans": {"Book": "path"}}
        sizes = {"62": "Label"}
        printers = []
        cfg = {
            "PRINTER": {"PRINTER": ""},
            "LABEL": {"DEFAULT_FONTS": [], "DEFAULT_SIZE": "62"},
        }

        errors = brother_ql_web.validate_configuration(fonts, sizes, printers, cfg)
        self.assertIn("No printers detected", " ".join(errors))

    def test_validate_flags_configured_printer_not_found(self):
        fonts = {"DejaVu Sans": {"Book": "path"}}
        sizes = {"62": "Label"}
        printers = ["p1"]
        cfg = {
            "PRINTER": {"PRINTER": "other"},
            "LABEL": {"DEFAULT_FONTS": [], "DEFAULT_SIZE": "62"},
        }

        errors = brother_ql_web.validate_configuration(fonts, sizes, printers, cfg)
        self.assertIn("Configured default printer 'other' not found", " ".join(errors))


if __name__ == "__main__":
    unittest.main()
