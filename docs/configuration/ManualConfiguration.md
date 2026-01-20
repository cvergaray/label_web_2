# Manual Configuration Guide

When manually editing the config.json to configuring the application, you can choose between a **minimal configuration** that relies on CUPS for most printer settings, or a **full configuration** that defines all printer and media settings explicitly.
The minimal configuration is simpler to set up and maintain, while the full configuration provides more control and backward compatibility.

Using the settings page will manage all of these settings for you. This guide is for users who prefer to edit the configuration file directly.

## Overview

This application requires a connection to a CUPS server (either on localhost or a remote server). The configuration controls whether the application dynamically queries CUPS for printer and media information, or uses static values from the configuration file.

**Note:** A CUPS server connection is always required for printing. The `USE_CUPS` flag only controls whether printer metadata is queried dynamically or defined statically in the configuration.

## Configuration file

Copy `config.example.json` to `config.json` (e.g. `cp config.example.json config.json`) and adjust the values 
to match your needs. You can still let the Settings UI generate/update this file for you, even after manual edits.

There are some printer-specific settings to include in config.json:

- `LABEL_SIZES`, a dictionary of items with a key and the human-readable description of that size
- `LABEL_PRINTABLE_AREA`, a dictionary of items mapping the same keys to the printable area in DPI
- `PRINTER`, the name of the default printer to be used as exposed by CUPS
- `DEFAULT_SIZE`, the key of the size from the `LABEL_SIZES` that should be used by default.

---

## Minimal Configuration File

See `config.minimal.json` for a minimal working configuration:

```json
{
  "SERVER": {
    "HOST": "0.0.0.0",
    "LOGLEVEL": "INFO"
  },
  "PRINTER": {
    "USE_CUPS": true,
    "SERVER": "192.168.1.176"
  },
  "LABEL": {
    "DEFAULT_ORIENTATION": "standard",
    "DEFAULT_FONT_SIZE": 70,
    "DEFAULT_FONTS": [
      {"family": "DejaVu Sans", "style": "Book"}
    ]
  },
  "WEBSITE": {
    "HTML_TITLE": "Label Designer",
    "PAGE_TITLE": "Label Designer",
    "PAGE_HEADLINE": "Design and print labels"
  }
}
```

## USE_CUPS Configuration Flag

The `USE_CUPS` flag in the `PRINTER` section controls whether the application queries CUPS for printer information or uses only the configuration file.

**Important:** A CUPS server connection is always required. This flag only controls whether printer metadata is queried from CUPS or defined in the configuration.

### USE_CUPS: true (Dynamic Mode - Recommended)
When enabled, the application queries CUPS for:
- Available printers
- Media sizes for each printer
- Default media size
- Media dimensions
- Printer resolution

**Best for:** All production environments (recommended default for new deployments)

### USE_CUPS: false (Static Mode)
When disabled, the application uses only configuration values:
- Uses `PRINTER.PRINTER` for printer name
- Uses `PRINTER.LABEL_SIZES` for media options
- Uses `LABEL.DEFAULT_SIZE` for default media
- Uses `PRINTER.LABEL_PRINTABLE_AREA` for dimensions

**Best for:** Backward compatibility with existing configurations

**Default:** `false` (for backward compatibility only - `true` is recommended for new deployments)

**Note:** Even with `USE_CUPS: false`, a CUPS server connection is still required for actual printing operations.

## What's Omitted (Retrieved from CUPS)

When using the minimal configuration, these settings are automatically retrieved from CUPS:

### Printer Information
- **Printer list**: Retrieved via `conn.getPrinters()`
- **Default printer**: Retrieved via `conn.getDefault()` or first available printer
- **Available media sizes**: Retrieved via `media-supported` attribute
- **Default media size**: Retrieved via `media-default` attribute
- **Media dimensions**: Retrieved via `media-size-supported` attribute
- **Printer resolution**: Retrieved via `printer-resolution-default` attribute

### What This Means
You don't need to configure:
- ❌ `PRINTER.PRINTER` - Auto-detected from CUPS
- ❌ `PRINTER.LABEL_SIZES` - Retrieved from each printer
- ❌ `PRINTER.LABEL_PRINTABLE_AREA` - Calculated from CUPS media dimensions
- ❌ `LABEL.DEFAULT_SIZE` - Retrieved from printer's default media

## Required Settings

### SERVER Section
```json
"SERVER": {
  "HOST": "0.0.0.0",           // Listen on all interfaces (use "localhost" for local only)
  "LOGLEVEL": "INFO"           // Logging level: DEBUG, INFO, WARNING, ERROR
}
```

**Optional:**
- `ADDITIONAL_FONT_FOLDER`: Path to additional fonts (default: false)

### PRINTER Section
```json
"PRINTER": {
  "USE_CUPS": true,            // Enable CUPS queries (default: false)
  "SERVER": "192.168.1.176"    // CUPS server address (always required)
}
```

**Required:**
- `USE_CUPS`: Boolean flag to enable/disable CUPS queries (defaults to `false`)
- `SERVER`: CUPS server address (required in both modes)

**Required if `USE_CUPS` is `false`:**
- `PRINTER`: Specific printer name to use as default
- `LABEL_SIZES`: Manual media size definitions
- `LABEL_PRINTABLE_AREA`: Manual dimension definitions

**Optional if `USE_CUPS` is `true`:**
- `PRINTER`: Force a specific default printer (otherwise auto-detected)

**Used as fallback if `USE_CUPS` is `true` and CUPS query fails:**
- `LABEL_SIZES`: Fallback media sizes if CUPS unavailable
- `LABEL_PRINTABLE_AREA`: Fallback dimensions if CUPS unavailable

**Note:** With `USE_CUPS: true`, CUPS media sizes are used exclusively when available. Config values are only used if CUPS queries fail.

### LABEL Section
```json
"LABEL": {
  "DEFAULT_ORIENTATION": "standard",  // or "rotated"
  "DEFAULT_FONT_SIZE": 70,            // Default font size in points
  "DEFAULT_FONTS": [                  // Fallback fonts to try (in order)
    {"family": "DejaVu Sans", "style": "Book"}
  ]
}
```

**Optional:**
- `DEFAULT_SIZE`: Specific default media (omit to use printer's default)

### WEBSITE Section
```json
"WEBSITE": {
  "HTML_TITLE": "Label Designer",      // Browser tab title
  "PAGE_TITLE": "Label Designer",      // Page header
  "PAGE_HEADLINE": "Design and print labels"  // Subtitle
}
```

## Full Configuration (config.example.json)

Use the full configuration with `USE_CUPS: false` when:

### 1. Backward Compatibility Required
If you have existing configurations that define printer settings:

```json
"PRINTER": {
  "USE_CUPS": false,
  "SERVER": "192.168.1.176",
  "PRINTER": "MyPrinter",
  "LABEL_SIZES": {
    "4x6": "4\" x 6\"",
    "3x1": "3\" x 1\""
  },
  "LABEL_PRINTABLE_AREA": {
    "4x6": [812, 1218],
    "3x1": [609, 203]
  }
}
```

**Note:** CUPS server connection is still required for printing.

### 2. Custom Media Sizes Not in CUPS
If you need to define custom media sizes that are not available in CUPS:

```json
"PRINTER": {
  "USE_CUPS": false,
  "SERVER": "192.168.1.176",
  "PRINTER": "Zebra-LP2844",
  "LABEL_SIZES": {
    "custom": "Custom 5x3",       // Define custom media
    "4x6": "4\" x 6\""
  },
  "LABEL_PRINTABLE_AREA": {
    "custom": [1015, 609],        // Define custom dimensions
    "4x6": [812, 1218]
  }
},
"LABEL": {
  "DEFAULT_SIZE": "custom"       // Use custom as default
}
```

**Note:** With `USE_CUPS: false`, you have complete control over which media sizes are available. Config values are used exclusively (CUPS metadata is not queried).

## Configuration Priority

The application uses the following priority for settings:

### Printer Selection
1. Query string parameter `?printer=Name`
2. `PRINTER.PRINTER` in config
3. First printer from CUPS (if `USE_CUPS` is `true`)
4. Error if no printers found

### Media Sizes
1. CUPS `media-supported` for selected printer (if `USE_CUPS` is `true`)
2. `PRINTER.LABEL_SIZES` from config (fallback, or primary if `USE_CUPS` is `false`)
3. Error if neither available

### Default Media
1. CUPS `media-default` for selected printer (if `USE_CUPS` is `true`)
2. `LABEL.DEFAULT_SIZE` from config (fallback, or primary if `USE_CUPS` is `false`)
3. First available media size

### Media Dimensions
1. CUPS `media-size-supported` (exact dimensions - if `USE_CUPS` is `true`)
2. Parse from media name (e.g., "4x6in")
3. `PRINTER.LABEL_PRINTABLE_AREA` from config
4. Default (300, 200) pixels

## Migration from Full to Minimal

If you're currently using a full configuration and want to switch to minimal:

### Step 1: Remove Redundant Settings
Remove these sections if CUPS provides them:
- `PRINTER.PRINTER` (unless you want to force a specific printer)
- `PRINTER.LABEL_SIZES` (CUPS provides this)
- `PRINTER.LABEL_PRINTABLE_AREA` (CUPS provides this)
- `LABEL.DEFAULT_SIZE` (CUPS provides this)

### Step 2: Test
1. Start the application with minimal config
2. Check that printers appear in dropdown
3. Check that media sizes load for each printer
4. Verify printing works with correct media

## Troubleshooting

### "No printers found"
- Check `PRINTER.SERVER` is correct (localhost or IP)
- Verify CUPS is running: `systemctl status cups`
- Check firewall allows CUPS port 631

### "No media sizes available"
- Check printer has media configured in CUPS
- Verify with: `lpoptions -p PrinterName -l`
- Add manual `LABEL_SIZES` as fallback

### "Dimensions incorrect"
- Check printer DPI: should auto-detect from CUPS
- Verify media-size-supported: `lpstat -p -v`
- Add manual `LABEL_PRINTABLE_AREA` if needed

### "Default media not selected"
- Check printer's default media in CUPS
- Set with: `lpoptions -p PrinterName -o media=4x6`
- Or specify `LABEL.DEFAULT_SIZE` in config

## Recommendations

Use **minimal configuration** with `USE_CUPS: true` (recommended):
- ✅ Auto-adapts to printer changes
- ✅ Always uses current printer settings
- ✅ Less configuration to maintain
- ✅ Works with any CUPS printer
- ✅ Preferred mode for new deployments

Use `USE_CUPS: false` only for:
- 🔄 Backward compatibility with existing configurations
- 🔧 When you need to define custom media sizes not in CUPS

**Note:** CUPS server connection is required in both modes.

## Example Scenarios

### Scenario 1: Office with CUPS Server
```json
{
  "SERVER": {"HOST": "0.0.0.0", "LOGLEVEL": "WARNING"},
  "PRINTER": {
    "USE_CUPS": true,
    "SERVER": "192.168.1.176"
  },
  "LABEL": {
    "DEFAULT_ORIENTATION": "standard",
    "DEFAULT_FONT_SIZE": 70,
    "DEFAULT_FONTS": [{"family": "Arial", "style": "Regular"}]
  },
  "WEBSITE": {
    "HTML_TITLE": "Office Labels",
    "PAGE_TITLE": "Office Label Printer",
    "PAGE_HEADLINE": "Print shipping and inventory labels"
  }
}
```

### Scenario 2: Standalone Raspberry Pi
```json
{
  "SERVER": {"HOST": "0.0.0.0", "LOGLEVEL": "INFO"},
  "PRINTER": {
    "USE_CUPS": true,
    "SERVER": "localhost",
    "PRINTER": "Zebra-LP2844"
  },
  "LABEL": {
    "DEFAULT_ORIENTATION": "standard",
    "DEFAULT_FONT_SIZE": 60,
    "DEFAULT_FONTS": [{"family": "DejaVu Sans", "style": "Book"}]
  },
  "WEBSITE": {
    "HTML_TITLE": "Label Printer",
    "PAGE_TITLE": "Label Printer",
    "PAGE_HEADLINE": "Print labels"
  }
}
```

### Scenario 3: Docker Container with Remote CUPS
```json
{
  "SERVER": {"HOST": "0.0.0.0", "LOGLEVEL": "WARNING"},
  "PRINTER": {
    "USE_CUPS": true,
    "SERVER": "192.168.1.100"
  },
  "LABEL": {
    "DEFAULT_ORIENTATION": "standard",
    "DEFAULT_FONT_SIZE": 70,
    "DEFAULT_FONTS": [{"family": "Liberation Sans", "style": "Regular"}]
  },
  "WEBSITE": {
    "HTML_TITLE": "Label Service",
    "PAGE_TITLE": "Label Printing Service",
    "PAGE_HEADLINE": "Cloud label printing"
  }
}
```

### Scenario 4: Static Configuration (Backward Compatibility)
```json
{
  "SERVER": {"HOST": "0.0.0.0", "LOGLEVEL": "INFO"},
  "PRINTER": {
    "USE_CUPS": false,
    "SERVER": "192.168.1.176",
    "PRINTER": "Zebra-LP2844",
    "LABEL_SIZES": {
      "4x6": "4\" x 6\"",
      "3x1": "3\" x 1\""
    },
    "LABEL_PRINTABLE_AREA": {
      "4x6": [812, 1218],
      "3x1": [609, 203]
    }
  },
  "LABEL": {
    "DEFAULT_SIZE": "4x6",
    "DEFAULT_ORIENTATION": "standard",
    "DEFAULT_FONT_SIZE": 70,
    "DEFAULT_FONTS": [{"family": "DejaVu Sans", "style": "Book"}]
  },
  "WEBSITE": {
    "HTML_TITLE": "Label Printer",
    "PAGE_TITLE": "Static Configuration Label Printer",
    "PAGE_HEADLINE": "Print labels"
  }
}
```

**Note:** Even with `USE_CUPS: false`, the `SERVER` setting is required for CUPS connection to print.

## Summary

The minimal configuration approach with `USE_CUPS: true`:
- 🎯 Simplifies setup and maintenance
- 🔄 Auto-adapts to printer configuration changes
- 🚀 Faster deployment to new environments
- 📊 Reduces configuration errors
- ✨ Leverages CUPS for all printer-specific settings
- ⭐ Recommended for all new deployments

Start with `config.minimal.json` (`USE_CUPS: true`) for the best experience. Use `config.example.json` (`USE_CUPS: false`) only when you need backward compatibility with existing configurations or want to define custom media sizes.

**Remember:** A CUPS server connection is required in both modes.

