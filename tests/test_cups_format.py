#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for CUPS media format parsing/validation behavior."""

import re
import unittest

from constants import PARSEABLE_SIZE_PATTERN


class TestCupsFormat(unittest.TestCase):
    def test_cups_format_validation(self):
        test_cases = [
            ("Custom.4x6in", "Custom.4x6in"),
            ("Custom.100x50mm", "Custom.100x50mm"),
            ("Custom.8x4cm", "Custom.8x4cm"),
            ("Custom.288x144pt", None),
            ("Custom.288x144", "Custom.288x144"),
            ("4x6in", "Custom.4x6in"),
            ("100x50mm", "Custom.100x50mm"),
            ("8x4cm", "Custom.8x4cm"),
            ("288x144pt", None),
            ("288x144", "Custom.288x144"),
            ("4 x 6 in", "Custom.4x6in"),
            ("4.5x6.5in", "Custom.4.5x6.5in"),
            ("100.5x50.5mm", "Custom.100.5x50.5mm"),
        ]

        for input_key, expected in test_cases:
            result = None
            if input_key.startswith('Custom.'):
                size_part = input_key[7:]
                match = re.search(PARSEABLE_SIZE_PATTERN, size_part, re.IGNORECASE)
                if match:
                    result = input_key
            else:
                match = re.search(PARSEABLE_SIZE_PATTERN, input_key, re.IGNORECASE)
                if match:
                    w, h, unit = match.groups()
                    result = f"Custom.{w}x{h}{unit.lower()}" if unit else f"Custom.{w}x{h}"
            self.assertEqual(result, expected)

    def test_unit_conversions(self):
        units = [
            ("in", "inches"),
            ("mm", "millimeters"),
            ("cm", "centimeters"),
            (None, "points (implicit)"),
        ]

        failures = []
        for unit, description in units:
            test_size = f"4x6{unit}" if unit else "288x144"
            match = re.search(PARSEABLE_SIZE_PATTERN, test_size, re.IGNORECASE)
            if not match:
                failures.append(f"{description}: '{test_size}' did not match pattern")
                continue
            _, _, matched_unit = match.groups()
            if not ((unit is None and matched_unit is None) or (unit == matched_unit)):
                failures.append(f"{description}: expected unit {unit!r}, got {matched_unit!r}")

        self.assertFalse(failures, "Unit recognition failures: " + "; ".join(failures))

    def test_explicit_pt_suffix_is_not_parseable(self):
        self.assertIsNone(re.search(PARSEABLE_SIZE_PATTERN, "288x144pt", re.IGNORECASE))
        self.assertIsNone(re.search(PARSEABLE_SIZE_PATTERN, "Custom.288x144pt", re.IGNORECASE))


if __name__ == "__main__":
    unittest.main()
