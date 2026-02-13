"""
Test script to verify DPI retrieval from implementation_cups.py
"""
from unittest.mock import MagicMock, patch
import sys
import os

# Mock the cups module before importing implementation_cups
sys.modules['cups'] = MagicMock()

from implementation_cups import implementation

def test_get_printer_dpi():
    """Test that _get_printer_dpi prioritizes config over CUPS"""

    print("Test 1: DPI from config takes priority")
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

    dpi = impl._get_printer_dpi('printer1')
    assert dpi == 300, f"Expected 300 DPI from config, got {dpi}"
    print(f"✓ Got DPI {dpi} from config for printer1")

    dpi = impl._get_printer_dpi('printer2')
    assert dpi == 600, f"Expected 600 DPI from config, got {dpi}"
    print(f"✓ Got DPI {dpi} from config for printer2")

    print("\nTest 2: DPI falls back to default when not in config")
    dpi = impl._get_printer_dpi('printer3')
    assert dpi == 203, f"Expected 203 DPI as default, got {dpi}"
    print(f"✓ Got default DPI {dpi} for printer3 (not in config)")

    print("\nTest 3: Config with no DPI section uses default")
    impl.CONFIG = {'PRINTER': {'PRINTER': 'printer1'}}
    dpi = impl._get_printer_dpi('printer1')
    assert dpi == 203, f"Expected 203 DPI as default, got {dpi}"
    print(f"✓ Got default DPI {dpi} when no DPI section in config")

    print("\nTest 4: CUPS resolution unit conversion")
    # Mock CUPS to return resolution in different units
    impl.CONFIG = {'PRINTER': {}}  # No DPI config
    impl.selected_printer = 'test-printer'

    # Test unit 3 (DPI) - should return as-is
    with patch.object(impl, '_get_conn') as mock_conn:
        mock_attrs = {'printer-resolution-default': (203, 203, 3)}
        mock_conn.return_value.getPrinterAttributes.return_value = mock_attrs
        dpi = impl._get_printer_dpi('test-printer')
        assert dpi == 203, f"Expected 203 DPI (unit 3), got {dpi}"
        print(f"✓ Unit 3 (DPI): Got {dpi} DPI")

    # Test unit 4 (DPCM) - should convert to DPI
    with patch.object(impl, '_get_conn') as mock_conn:
        # 80 DPCM = 203.2 DPI (80 * 2.54)
        mock_attrs = {'printer-resolution-default': (80, 80, 4)}
        mock_conn.return_value.getPrinterAttributes.return_value = mock_attrs
        dpi = impl._get_printer_dpi('test-printer')
        assert dpi == 203, f"Expected 203 DPI (converted from 80 DPCM), got {dpi}"
        print(f"✓ Unit 4 (DPCM): Converted 80 DPCM to {dpi} DPI")

    # Test unknown unit - should assume DPI
    with patch.object(impl, '_get_conn') as mock_conn:
        mock_attrs = {'printer-resolution-default': (300, 300, 99)}
        mock_conn.return_value.getPrinterAttributes.return_value = mock_attrs
        dpi = impl._get_printer_dpi('test-printer')
        assert dpi == 300, f"Expected 300 DPI (unknown unit assumed DPI), got {dpi}"
        print(f"✓ Unknown unit: Assumed DPI and got {dpi}")

    print("\nTest 5: Priority order (config > CUPS > default)")
    impl.CONFIG = {
        'PRINTER': {
            'DPI': {'test-printer': 999}  # Config overrides CUPS
        }
    }
    with patch.object(impl, '_get_conn') as mock_conn:
        mock_attrs = {'printer-resolution-default': (300, 300, 3)}
        mock_conn.return_value.getPrinterAttributes.return_value = mock_attrs
        dpi = impl._get_printer_dpi('test-printer')
        assert dpi == 999, f"Expected 999 DPI from config (overriding CUPS 300), got {dpi}"
        print(f"✓ Config DPI {dpi} took priority over CUPS 300")

    print("\n" + "="*50)
    print("All _get_printer_dpi tests passed! ✓")
    print("="*50)

if __name__ == '__main__':
    test_get_printer_dpi()

