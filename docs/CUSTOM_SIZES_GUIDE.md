# Custom Label Sizes Configuration Guide

This guide explains how to configure custom label sizes for use with CUPS printers.

## Overview

Custom label sizes can be defined in three ways:
1. **In the CUPS server** (recommended for permanent sizes)
2. **In the config.json file** (for application-specific sizes)
3. **Using parseable size names** (automatic dimension calculation)

## Method 1: CUPS Server Custom Sizes

Define custom media sizes directly in your CUPS server configuration. These will be automatically detected and available in the application.

**Advantages:**
- Centralized configuration
- Works across all applications using the printer
- Automatically includes precise dimensions

**How it works:**
The application queries the CUPS printer for `media-supported` and `media-size-supported` attributes, which include both standard and custom sizes.

## Method 2: Config File Custom Sizes

Add custom sizes to your `config.json` file under the `PRINTER` section.

### Basic Configuration

```json
{
  "PRINTER": {
    "USE_CUPS": true,
    "LABEL_SIZES": {
      "Custom.3x1in": "3\" by 1\"",
      "custom_large": "Large Custom Label"
    }
  }
}
```

### Recommended Configuration (with explicit dimensions)

```json
{
  "PRINTER": {
    "USE_CUPS": true,
    "LABEL_SIZES": {
      "3x1in": "3\" by 1\"",
      "4x6in": "4 inch by 6 inch",
      "custom_large": "Large Custom Label"
    },
    "LABEL_PRINTABLE_AREA": {
      "3x1in": [609, 203],
      "4x6in": [812, 1218],
      "custom_large": [800, 400]
    }
  }
}
```

### Calculating Dimensions

Dimensions in `LABEL_PRINTABLE_AREA` should be in **pixels** based on your printer's DPI.

**Formula:** `pixels = inches × DPI`

**Common DPI values:**
- Thermal label printers: 203 DPI (default)
- High-resolution thermal: 300 DPI
- Desktop printers: 600 DPI

**Examples:**

For a **3" × 1"** label at **203 DPI**:
- Width: 3 × 203 = 609 pixels
- Height: 1 × 203 = 203 pixels
- Config: `"3x1": [609, 203]`

For a **4" × 6"** label at **203 DPI**:
- Width: 4 × 203 = 812 pixels
- Height: 6 × 203 = 1218 pixels
- Config: `"4x6in": [812, 1218]`

For a **100mm × 50mm** label at **203 DPI**:
- Width: (100 / 25.4) × 203 = 799 pixels
- Height: (50 / 25.4) × 203 = 400 pixels
- Config: `"100x50mm": [799, 400]`

## Method 3: Parseable Size Names

Use size keys that include dimensions in the name. The application will automatically parse and calculate pixel dimensions.

**Supported formats:**
- `Custom.WxHin` - Width × Height in inches (e.g., "4x6in")
- `Custom.WxHmm` - Width × Height in millimeters (e.g., "100x50mm")

**Example:**

```json
{
  "PRINTER": {
    "LABEL_SIZES": {
      "4x6in": "4 inch by 6 inch Label",
      "100x50mm": "100mm by 50mm Label"
    }
  }
}
```

No need to define `LABEL_PRINTABLE_AREA` - dimensions are calculated automatically!

## Configuration Priority

When dimensions are needed, the system checks in this order:

1. **CUPS media-size-supported** - Precise dimensions from CUPS
2. **Parse size name** - Extract from names like "Custom.4x6in"
3. **Config LABEL_PRINTABLE_AREA** - Explicit config values
4. **Default size** - Falls back to 300×200 pixels

## Complete Example

```json
{
  "SERVER": {
    "HOST": "0.0.0.0",
    "LOGLEVEL": "INFO"
  },
  "PRINTER": {
    "USE_CUPS": true,
    "SERVER": "192.168.1.100",
    "PRINTER": "Zebra-LP2844",
    "LABEL_SIZES": {
      "Custom.2x1in": "2\" × 1\" Address Label",
      "Custom.3x1in": "3\" × 1\" Address Label",
      "Custom.4x6in": "4\" × 6\" Shipping Label",
      "custom_square": "Custom Square Label"
    },
    "LABEL_PRINTABLE_AREA": {
      "custom_square": [600, 600]
    }
  },
  "LABEL": {
    "DEFAULT_SIZE": "Custom.3x1in"
  }
}
```

In this example:
- `Custom.2x1in`, `Custom.3x1in`, `Custom.4x6in` - Dimensions parsed from names
- `custom_square` - Explicit dimensions provided (600×600 pixels)

## Merging with CUPS Sizes

When `USE_CUPS: true`, the application will:

1. Query CUPS for all supported media sizes (including CUPS custom sizes)
2. Load custom sizes from config
3. Merge both lists
4. Remove duplicates (CUPS sizes take precedence)

This means you'll see:
- All standard CUPS media
- Custom CUPS media (defined in printer PPD or CUPS server)
- Custom config media (that don't duplicate CUPS sizes)

## Troubleshooting

### Size not appearing in web interface?

Check console output for:
- `"Info: Using dimensions from CUPS..."` - Size found in CUPS
- `"Info: Using dimensions from config..."` - Size found in config
- `"Warning: No dimensions found..."` - Size not found anywhere

### Label printing with wrong size?

Check console output when printing for:
- `"Info: Using custom config size..."` - Custom size being used
- `"Warning: Selected media '...' not available..."` - Size not recognized

### Dimensions incorrect?

1. Verify your printer DPI (default is 203)
2. Double-check calculations for LABEL_PRINTABLE_AREA
3. Use parseable names for automatic calculation
4. Check console logs to see which dimension source was used

## Tips

✅ **Use parseable names** like "4x6in" for automatic dimension calculation  
✅ **Provide explicit dimensions** in LABEL_PRINTABLE_AREA for precise control  
✅ **Test with logging enabled** to see dimension sources  
✅ **Define custom sizes in CUPS** for permanent, cross-application support  
✅ **Use config for temporary** or application-specific sizes  

## Reference Links

- CUPS Media Standardized Names: https://www.cups.org/doc/spec-ppd.html
- CUPS API Documentation: https://www.cups.org/doc/api-cups.html

