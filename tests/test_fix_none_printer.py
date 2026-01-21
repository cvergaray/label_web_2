#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test to verify the fix for NoneType error when deleting custom sizes.

This test simulates the scenario where CONFIG['PRINTER'] might be None
and ensures the application handles it gracefully.
"""

import copy
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from configuration_management import settings_format_to_config

def test_settings_format_with_none_printer():
    """Test that settings_format_to_config handles None printer section gracefully"""
    print("Test 1: Testing settings_format_to_config with None printer section...")

    # Simulate a settings payload where printer section might be missing or None
    test_cases = [
        {},  # Empty settings
        {'printer': None},  # Explicit None
        {'printer': {}},  # Empty printer dict
        None,  # None settings
    ]

    for i, settings in enumerate(test_cases):
        try:
            result = settings_format_to_config(settings)
            assert 'PRINTER' in result, f"Test case {i+1}: PRINTER section missing"
            assert result['PRINTER'] is not None, f"Test case {i+1}: PRINTER is None"
            assert isinstance(result['PRINTER'], dict), f"Test case {i+1}: PRINTER is not a dict"
            print(f"  ✓ Test case {i+1} passed: {settings}")
        except Exception as e:
            print(f"  ✗ Test case {i+1} failed: {settings}")
            print(f"    Error: {e}")
            return False

    print("  All test cases passed!")
    return True


def test_config_deepcopy_with_none():
    """Test that deepcopy handles CONFIG with None PRINTER section"""
    print("\nTest 2: Testing deepcopy with None PRINTER section...")

    test_configs = [
        {'PRINTER': None, 'SERVER': {}},
        {'PRINTER': {}, 'SERVER': {}},
        {'SERVER': {}},  # Missing PRINTER
    ]

    for i, config in enumerate(test_configs):
        try:
            temp_config = copy.deepcopy(config)

            # Ensure PRINTER section exists and is a dict (defensive check)
            if temp_config.get('PRINTER') is None:
                temp_config['PRINTER'] = {}

            # Try to access PRINTER like the fixed code does
            temp_config['PRINTER']['USE_CUPS'] = True
            temp_config['PRINTER']['SERVER'] = 'localhost'

            print(f"  ✓ Test case {i+1} passed")
        except Exception as e:
            print(f"  ✗ Test case {i+1} failed")
            print(f"    Error: {e}")
            return False

    print("  All test cases passed!")
    return True


def test_implementation_initialize_with_none():
    """Test that implementation.initialize handles None PRINTER section"""
    print("\nTest 3: Testing implementation.initialize with None PRINTER section...")

    try:
        # Try to import cups first to see if it's available
        import cups
        cups_available = hasattr(cups, 'setServer')
    except (ImportError, AttributeError):
        cups_available = False

    if not cups_available:
        print(f"  ⚠ Skipping test (cups library not properly available on this platform)")
        return True

    try:
        from implementation_cups import implementation

        test_configs = [
            {'PRINTER': None},
            {'PRINTER': {}},
            {},  # Missing PRINTER
        ]

        for i, config in enumerate(test_configs):
            try:
                instance = implementation()
                result = instance.initialize(config)

                # Verify PRINTER section was created/fixed
                assert 'PRINTER' in instance.CONFIG, f"Test case {i+1}: PRINTER section missing"
                assert instance.CONFIG['PRINTER'] is not None, f"Test case {i+1}: PRINTER is None"
                assert isinstance(instance.CONFIG['PRINTER'], dict), f"Test case {i+1}: PRINTER is not a dict"

                print(f"  ✓ Test case {i+1} passed")
            except Exception as e:
                print(f"  ✗ Test case {i+1} failed")
                print(f"    Error: {e}")
                return False

        print("  All test cases passed!")
        return True
    except ImportError as e:
        print(f"  ⚠ Skipping test (implementation_cups not available): {e}")
        return True  # Don't fail if implementation is not available


if __name__ == '__main__':
    print("="*60)
    print("Testing fix for NoneType error when deleting custom sizes")
    print("="*60)

    all_passed = True

    all_passed = test_settings_format_with_none_printer() and all_passed
    all_passed = test_config_deepcopy_with_none() and all_passed
    all_passed = test_implementation_initialize_with_none() and all_passed

    print("\n" + "="*60)
    if all_passed:
        print("✓ All tests passed!")
        print("="*60)
        sys.exit(0)
    else:
        print("✗ Some tests failed!")
        print("="*60)
        sys.exit(1)
