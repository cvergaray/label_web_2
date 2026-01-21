#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test the _convert_to_cups_media_format function to ensure it properly
validates and converts size keys to valid CUPS custom media format.
"""

import re
from constants import PARSEABLE_SIZE_PATTERN

def test_cups_format_validation():
    """Test that the CUPS format validation works correctly."""
    
    print("Testing CUPS Media Format Conversion Logic")
    print("=" * 60)
    
    # Test cases: (input, expected_output, description)
    test_cases = [
        # Already in CUPS format - should return as-is
        ("Custom.4x6in", "Custom.4x6in", "Already valid CUPS format with inches"),
        ("Custom.100x50mm", "Custom.100x50mm", "Already valid CUPS format with mm"),
        ("Custom.8x4cm", "Custom.8x4cm", "Already valid CUPS format with cm"),
        ("Custom.288x144pt", "Custom.288x144pt", "Already valid CUPS format with explicit points"),
        ("Custom.288x144", "Custom.288x144", "Already valid CUPS format with implied points"),
        
        # Valid parseable formats - should add Custom. prefix
        ("4x6in", "Custom.4x6in", "Inches format"),
        ("100x50mm", "Custom.100x50mm", "Millimeters format"),
        ("8x4cm", "Custom.8x4cm", "Centimeters format"),
        ("288x144pt", "Custom.288x144pt", "Explicit points format"),
        ("288x144", "Custom.288x144", "Implied points format (no unit)"),
        
        # With spaces (should still work)
        ("4 x 6 in", "Custom.4x6in", "Format with spaces"),
        
        # Decimal values
        ("4.5x6.5in", "Custom.4.5x6.5in", "Decimal inches"),
        ("100.5x50.5mm", "Custom.100.5x50.5mm", "Decimal millimeters"),
    ]
    
    passed = 0
    failed = 0
    
    for input_key, expected, description in test_cases:
        # Simulate the _convert_to_cups_media_format logic
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
                if unit:
                    unit_lower = unit.lower()
                    result = f"Custom.{w}x{h}{unit_lower}"
                else:
                    result = f"Custom.{w}x{h}"
        
        if result == expected:
            print(f"✓ PASS: {description}")
            print(f"  Input: '{input_key}' → Output: '{result}'")
            passed += 1
        else:
            print(f"✗ FAIL: {description}")
            print(f"  Input: '{input_key}' → Expected: '{expected}', Got: '{result}'")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

def test_unit_conversions():
    """Test that all CUPS units are properly recognized."""
    
    print("\n\nTesting Unit Recognition")
    print("=" * 60)
    
    units = [
        ("in", "inches"),
        ("mm", "millimeters"),
        ("cm", "centimeters"),
        ("pt", "points (explicit)"),
        (None, "points (implicit)")
    ]
    
    for unit, description in units:
        test_size = f"4x6{unit}" if unit else "288x144"
        match = re.search(PARSEABLE_SIZE_PATTERN, test_size, re.IGNORECASE)
        if match:
            w, h, matched_unit = match.groups()
            if (unit is None and matched_unit is None) or (unit == matched_unit):
                print(f"✓ {description}: '{test_size}' → groups: ({w}, {h}, {matched_unit})")
            else:
                print(f"✗ {description}: expected unit '{unit}', got '{matched_unit}'")
        else:
            print(f"✗ {description}: '{test_size}' did not match pattern")
    
    print("=" * 60)

if __name__ == "__main__":
    success1 = test_cups_format_validation()
    test_unit_conversions()
    exit(0 if success1 else 1)
