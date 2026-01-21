#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Shared constants for Label Web application.

This module contains constants that are used across multiple modules,
particularly validation patterns that should remain synchronized.
"""

# Regex pattern for validating parseable size keys
# Matches patterns like: "4x6in", "100x50mm", "3.5x2cm", "5 x 3 in", etc.
# Used in both backend (Python) and frontend (JavaScript) for consistent validation
#
# Pattern breakdown:
#   ^(\d+(?:\.\d+)?)  - Width: one or more digits, optionally followed by decimal point and more digits
#   \s*x\s*           - Letter 'x' (case-insensitive), optionally surrounded by whitespace
#   (\d+(?:\.\d+)?)   - Height: same format as width
#   \s*(in|mm|cm)?$   - Unit suffix: 'in', 'mm', or 'cm' (optional), case-insensitive
#
# SYNCHRONIZATION REQUIREMENTS:
# This pattern MUST be kept synchronized between backend and frontend implementations:
#
# Python (Backend):
#   - File: implementation_cups.py
#   - Import: from constants import PARSEABLE_SIZE_PATTERN
#   - Usage: re.search(PARSEABLE_SIZE_PATTERN, media_name, re.IGNORECASE)
#
# JavaScript (Frontend):
#   - File: views/settings.jinja2
#   - Pattern: /^(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(in|mm|cm)?$/i
#   - Usage: parseablePattern.test(sizeKey)
#
PARSEABLE_SIZE_PATTERN = r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(in|mm|cm)?'
