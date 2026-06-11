from pathlib import Path
import unittest


VIEWS_DIR = Path(__file__).resolve().parents[1] / "views"
BASE_VIEW = VIEWS_DIR / "base.jinja2"
TEMPLATEPRINT_VIEW = VIEWS_DIR / "templateprint.jinja2"
LABELDESIGNER_VIEW = VIEWS_DIR / "labeldesigner.jinja2"


class TestTemplatePrintPreview(unittest.TestCase):
    def test_base_view_cache_busts_common_js_after_preview_dpi_change(self):
        """The shared JS bundle should be cache-busted so browsers pick up new preview helpers."""
        content = BASE_VIEW.read_text(encoding="utf-8")
        self.assertIn('/static/js/common.js?v=20260603-preview-dpi', content)

    def test_template_preview_request_includes_selected_printer(self):
        """Template preview must send the selected printer for printer-specific DPI lookup."""
        content = TEMPLATEPRINT_VIEW.read_text(encoding="utf-8")
        self.assertIn("regularData['printer'] = $('#printer').val();", content)

    def test_template_preview_uses_effective_dpi_header_for_size_display(self):
        """Template preview size display should use the effective DPI returned by the server."""
        content = TEMPLATEPRINT_VIEW.read_text(encoding="utf-8")
        self.assertIn("typeof getEffectivePreviewDpi === 'function'", content)
        self.assertIn("getEffectivePreviewDpi(jqXHR, 300)", content)
        self.assertIn("typeof updatePrintedSizeDisplay === 'function'", content)
        self.assertIn("updatePrintedSizeDisplay(img, effectiveDpi);", content)

    def test_labeldesigner_preview_uses_effective_dpi_header_for_size_display(self):
        """Label designer should also use the effective DPI returned by the server."""
        content = LABELDESIGNER_VIEW.read_text(encoding="utf-8")
        self.assertIn("typeof getEffectivePreviewDpi === 'function'", content)
        self.assertIn("getEffectivePreviewDpi(jqXHR, 300)", content)
        self.assertIn("typeof updatePrintedSizeDisplay === 'function'", content)
        self.assertIn("updatePrintedSizeDisplay(img, effectiveDpi);", content)


if __name__ == '__main__':
    unittest.main()



