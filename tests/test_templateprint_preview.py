from pathlib import Path


VIEWS_DIR = Path(__file__).resolve().parents[1] / "views"
BASE_VIEW = VIEWS_DIR / "base.jinja2"
TEMPLATEPRINT_VIEW = VIEWS_DIR / "templateprint.jinja2"
LABELDESIGNER_VIEW = VIEWS_DIR / "labeldesigner.jinja2"


def test_base_view_cache_busts_common_js_after_preview_dpi_change():
    """The shared JS bundle should be cache-busted so browsers pick up new preview helpers."""
    content = BASE_VIEW.read_text(encoding="utf-8")

    assert '/static/js/common.js?v=20260603-preview-dpi' in content


def test_template_preview_request_includes_selected_printer():
    """Template preview must send the selected printer for printer-specific DPI lookup."""
    content = TEMPLATEPRINT_VIEW.read_text(encoding="utf-8")

    assert "regularData['printer'] = $('#printer').val();" in content


def test_template_preview_uses_effective_dpi_header_for_size_display():
    """Template preview size display should use the effective DPI returned by the server."""
    content = TEMPLATEPRINT_VIEW.read_text(encoding="utf-8")

    assert "typeof getEffectivePreviewDpi === 'function'" in content
    assert "getEffectivePreviewDpi(jqXHR, 300)" in content
    assert "typeof updatePrintedSizeDisplay === 'function'" in content
    assert "updatePrintedSizeDisplay(img, effectiveDpi);" in content


def test_labeldesigner_preview_uses_effective_dpi_header_for_size_display():
    """Label designer should also use the effective DPI returned by the server."""
    content = LABELDESIGNER_VIEW.read_text(encoding="utf-8")

    assert "typeof getEffectivePreviewDpi === 'function'" in content
    assert "getEffectivePreviewDpi(jqXHR, 300)" in content
    assert "typeof updatePrintedSizeDisplay === 'function'" in content
    assert "updatePrintedSizeDisplay(img, effectiveDpi);" in content



