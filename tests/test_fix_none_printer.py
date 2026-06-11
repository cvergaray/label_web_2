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
import unittest

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from configuration_management import settings_format_to_config

class TestFixNonePrinter(unittest.TestCase):
    def test_settings_format_with_none_printer(self):
        """settings_format_to_config should safely normalize missing/None printer sections."""
        test_cases = [
            {},
            {'printer': None},
            {'printer': {}},
            None,
        ]

        for i, settings in enumerate(test_cases):
            try:
                result = settings_format_to_config(settings)
                self.assertIn('PRINTER', result, f"Test case {i+1}: PRINTER section missing")
                self.assertIsNotNone(result['PRINTER'], f"Test case {i+1}: PRINTER is None")
                self.assertIsInstance(result['PRINTER'], dict, f"Test case {i+1}: PRINTER is not a dict")
            except Exception as e:
                self.fail(f"Test case {i+1} failed for settings {settings!r}: {e}")

    def test_config_deepcopy_with_none(self):
        """Deep copy workflows should remain safe when PRINTER starts as None."""
        test_configs = [
            {'PRINTER': None, 'SERVER': {}},
            {'PRINTER': {}, 'SERVER': {}},
            {'SERVER': {}},
        ]

        for i, config in enumerate(test_configs):
            try:
                temp_config = copy.deepcopy(config)
                if temp_config.get('PRINTER') is None:
                    temp_config['PRINTER'] = {}
                temp_config['PRINTER']['USE_CUPS'] = True
                temp_config['PRINTER']['SERVER'] = 'localhost'
            except Exception as e:
                self.fail(f"Deepcopy test case {i+1} failed for config {config!r}: {e}")

    def test_implementation_initialize_with_none(self):
        """implementation.initialize should tolerate None/missing PRINTER sections."""
        try:
            import cups
            cups_available = hasattr(cups, 'setServer')
        except (ImportError, AttributeError):
            cups_available = False

        if not cups_available:
            self.skipTest("cups library not properly available on this platform")

        try:
            from implementation_cups import implementation
        except ImportError as e:
            self.skipTest(f"implementation_cups not available: {e}")

        test_configs = [
            {'PRINTER': None},
            {'PRINTER': {}},
            {},
        ]

        for i, config in enumerate(test_configs):
            try:
                instance = implementation()
                instance.initialize(config)
                self.assertIn('PRINTER', instance.CONFIG, f"Test case {i+1}: PRINTER section missing")
                self.assertIsNotNone(instance.CONFIG['PRINTER'], f"Test case {i+1}: PRINTER is None")
                self.assertIsInstance(instance.CONFIG['PRINTER'], dict, f"Test case {i+1}: PRINTER is not a dict")
            except Exception as e:
                self.fail(f"Implementation initialize test case {i+1} failed for config {config!r}: {e}")


if __name__ == '__main__':
    unittest.main()
