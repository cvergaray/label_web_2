"""
Simple test script to verify DPI configuration feature.
"""
import json
import configuration_management as cm

def test_dpi_config():
    """Test that DPI configuration is properly converted between formats"""

    # Test 1: config_to_settings_format includes DPI
    print("Test 1: config_to_settings_format includes DPI")
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
    assert 'dpi' in settings['printer'], "DPI not found in settings printer section"
    assert settings['printer']['dpi'] == {'printer1': 203, 'printer2': 300}, "DPI values don't match"
    print("✓ DPI correctly converted to settings format")

    # Test 2: settings_format_to_config includes DPI
    print("\nTest 2: settings_format_to_config includes DPI")
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
    assert 'DPI' in config_result['PRINTER'], "DPI not found in config PRINTER section"
    assert config_result['PRINTER']['DPI'] == {'printer-a': 203, 'printer-b': 600}, "DPI values don't match"
    print("✓ DPI correctly converted to config format")

    # Test 3: Round-trip conversion preserves DPI
    print("\nTest 3: Round-trip conversion preserves DPI")
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

    assert final_config['PRINTER']['DPI'] == {'zebra': 203, 'dymo': 300}, "DPI not preserved in round-trip"
    print("✓ DPI preserved through round-trip conversion")

    # Test 4: Empty DPI handled correctly
    print("\nTest 4: Empty DPI handled correctly")
    config_no_dpi = {
        'SERVER': {},
        'PRINTER': {},
        'LABEL': {},
        'WEBSITE': {}
    }

    settings = cm.config_to_settings_format(config_no_dpi)
    assert 'dpi' in settings['printer'], "DPI key should exist even if empty"
    assert settings['printer']['dpi'] == {}, "Empty DPI should be empty dict"
    print("✓ Empty DPI handled correctly")

    print("\n" + "="*50)
    print("All DPI configuration tests passed! ✓")
    print("="*50)

if __name__ == '__main__':
    test_dpi_config()

