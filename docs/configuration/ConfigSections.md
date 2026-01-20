# Configuration Sections Reference

<!-- TOC -->
* [Configuration Sections Reference](#configuration-sections-reference)
  * [Overview](#overview)
  * [Configuration File Location](#configuration-file-location)
  * [Configuration Structure](#configuration-structure)
  * [SERVER Section](#server-section)
    * [SERVER.HOST](#serverhost)
    * [SERVER.PORT](#serverport)
    * [SERVER.LOGLEVEL](#serverloglevel)
    * [SERVER.ADDITIONAL_FONT_FOLDER](#serveradditional_font_folder)
  * [PRINTER Section](#printer-section)
    * [PRINTER.USE_CUPS](#printeruse_cups)
    * [PRINTER.SERVER](#printerserver)
    * [PRINTER.PRINTER](#printerprinter)
    * [PRINTER.LABEL_SIZES](#printerlabel_sizes)
    * [PRINTER.LABEL_PRINTABLE_AREA](#printerlabel_printable_area)
    * [PRINTER.ENABLED_SIZES](#printerenabled_sizes)
    * [PRINTER.PRINTERS_INCLUDE](#printerprinters_include)
    * [PRINTER.PRINTERS_EXCLUDE](#printerprinters_exclude)
  * [LABEL Section](#label-section)
    * [LABEL.DEFAULT_SIZE](#labeldefault_size)
    * [LABEL.DEFAULT_ORIENTATION](#labeldefault_orientation)
    * [LABEL.DEFAULT_FONT_SIZE](#labeldefault_font_size)
    * [LABEL.DEFAULT_FONTS](#labeldefault_fonts)
  * [WEBSITE Section](#website-section)
    * [WEBSITE.HTML_TITLE](#websitehtml_title)
    * [WEBSITE.PAGE_TITLE](#websitepage_title)
    * [WEBSITE.PAGE_HEADLINE](#websitepage_headline)
  * [Configuration Priority and Fallbacks](#configuration-priority-and-fallbacks)
    * [Printer Selection Priority](#printer-selection-priority)
    * [Media Size Priority](#media-size-priority)
    * [Default Media Selection Priority](#default-media-selection-priority)
    * [Media Dimensions Priority](#media-dimensions-priority)
  * [Corner Cases and Special Behaviors](#corner-cases-and-special-behaviors)
    * [Empty or Missing Default Printer](#empty-or-missing-default-printer)
    * [CUPS Server Connection Failures](#cups-server-connection-failures)
    * [Custom Media Sizes with CUPS](#custom-media-sizes-with-cups)
    * [Font Fallback Behavior](#font-fallback-behavior)
    * [Empty Configuration Sections](#empty-configuration-sections)
    * [LABEL_SIZES Format Compatibility](#label_sizes-format-compatibility)
    * [Initialization Errors](#initialization-errors)
    * [Configuration File Not Found](#configuration-file-not-found)
    * [Invalid JSON in Configuration](#invalid-json-in-configuration)
  * [Complete Configuration Examples](#complete-configuration-examples)
    * [Minimal CUPS Configuration](#minimal-cups-configuration)
    * [Full Static Configuration](#full-static-configuration)
    * [Hybrid Configuration](#hybrid-configuration)
    * [Multi-Printer Configuration with Filters](#multi-printer-configuration-with-filters)
<!-- TOC -->

## Overview

This document provides comprehensive details on every configuration section, property, default value, and corner case for the Label Designer application. The configuration controls server behavior, printer connectivity, label defaults, and UI appearance.

**Configuration Methods:**
1. **Settings UI (Recommended)**: Use the in-app Settings page to configure all options visually. Changes are saved to `config.json` automatically.
2. **Manual JSON (Advanced)**: Edit `config.json` directly with your preferred text editor and restart the application. (see the [ManualConfiguration](ManualConfiguration.md) guide.)

## Configuration File Location

The application searches for configuration files in this order:

1. `/appconfig/config.json` (Docker container default)
2. `config.json` (local directory)
3. `config.minimal.json` (fallback)

If no configuration file is found, the application uses built-in defaults and logs a warning. The Settings page can then be used to create a proper configuration, which will be saved to /appconfig/config.json.

## Configuration Structure

The configuration file is a JSON object with four top-level sections:

```json
{
  "SERVER": { /* Server settings */ },
  "PRINTER": { /* Printer and CUPS settings */ },
  "LABEL": { /* Label rendering defaults */ },
  "WEBSITE": { /* UI text and branding */ }
}
```

Although, each section is technically optional, as missing sections will use built-in defaults, it is highly 
recommended to include all sections for clarity and explicit configuration. This also protects against defaults changing
in future versions to something unexpected.

---

## SERVER Section

Controls the web service parameters, logging level, and font directories.

### SERVER.HOST

**Type**: `string`

**Description**: The network interface or IP address that the web service will bind to. This controls which network interfaces can access the application.

**Required**: No

**Default**: `"0.0.0.0"`

**Valid Values**:
- `"0.0.0.0"` - Bind to all available network interfaces (accessible from any IP)
- `"127.0.0.1"` or `"localhost"` - Bind to localhost only (accessible only from the same machine)
- Any valid IP address - Bind to a specific interface
- `""` (empty string) - Equivalent to `"0.0.0.0"`

**Examples**:

```json
{
  "SERVER": {
    "HOST": "0.0.0.0"
  }
}
```

```json
{
  "SERVER": {
    "HOST": "127.0.0.1"
  }
}
```

**Corner Cases**:
- Empty string is treated as `"0.0.0.0"`
- Invalid IP addresses may cause startup failure
- Using `localhost` or `127.0.0.1` prevents access from Docker containers or remote machines

---

### SERVER.PORT

**Type**: `integer`

**Description**: The TCP port number that the web service will listen on. 
This is the port you'll access in your browser. When in the container, this port may be mapped to a different external 
port using Docker's `-p` flag or `docker-compose` port mapping.

**Required**: No

**Default**: `8013`

**Valid Values**: Any valid TCP port number (1-65535). Ports below 1024 typically require root/admin privileges.

**Example**:

```json
{
  "SERVER": {
    "PORT": 8013
  }
}
```

**Usage Note**:
Docker port mapping can override this (e.g., `-p 80:8013` maps external port 80 to internal 8013). 
So, when running in Docker, you typically map this internal port to an external port using the `-p` flag.

---

### SERVER.LOGLEVEL

**Type**: `string`

**Description**: Controls the verbosity of application logging. Higher log levels provide more detailed information for debugging.

**Required**: No

**Default**: `"INFO"`

**Valid Values**:
- `"DEBUG"` - Most verbose; logs all messages including debugging details
- `"INFO"` - Standard logging; includes informational messages
- `"WARNING"` - Only warnings and errors
- `"ERROR"` - Only errors and critical issues
- `"CRITICAL"` - Only critical failures

**Example**:

```json
{
  "SERVER": {
    "LOGLEVEL": "INFO"
  }
}
```

**Usage Note**: 
- Use `DEBUG` when troubleshooting issues, `WARNING` for production to reduce log noise.
- Invalid log levels will default to `INFO`
- Log output goes to stdout/stderr (captured by Docker logs or terminal)

---

### SERVER.ADDITIONAL_FONT_FOLDER

**Type**: `string` or `false`

**Description**: Path to a directory containing additional TrueType (`.ttf`) or OpenType (`.otf`) font files. Fonts in this directory will be available for label rendering in addition to system fonts.

**Required**: No

**Default**: `"/fonts"`

**Valid Values**:
- Any valid file system path (absolute or relative)
- `false` - Disable additional font loading
- `""` (empty string) - Treated as disabled

**Examples**:

Load fonts from `/fonts` directory:
```json
{
  "SERVER": {
    "ADDITIONAL_FONT_FOLDER": "/fonts"
  }
}
```

Load fonts from custom path:
```json
{
  "SERVER": {
    "ADDITIONAL_FONT_FOLDER": "/custom/fonts/path"
  }
}
```

Disable additional fonts:
```json
{
  "SERVER": {
    "ADDITIONAL_FONT_FOLDER": false
  }
}
```

**Usage Note**:
- When using Docker, bind mount your font directory to `/fonts` or update this path to match your mounted volume.
- If path doesn't exist, the application logs a warning and continues (system fonts still available)
- Non-font files in the directory are ignored
- Fonts with invalid or corrupt data are skipped
- Duplicate font family/style names from additional folder override system fonts
- Path must be accessible with the application's user permissions


---

## PRINTER Section

Controls CUPS connectivity, printer discovery, media size management, and printer filtering.

### PRINTER.USE_CUPS

**Type**: `boolean`

**Description**: Controls whether the application dynamically queries the CUPS server for printer metadata 
(printers, media sizes, defaults) or uses only static values from the configuration file.

**Important**: A CUPS server connection is **always required** for printing, regardless of this setting. 
This flag only controls whether printer **metadata** is queried from CUPS.

**Required**: No

**Default**: `false` (for backward compatibility with existing configs)

**Valid Values**:
- `true` - Query CUPS for printer metadata (Dynamic Mode - Recommended)
- `false` - Use only configuration values (Static Mode)

**Dynamic Mode (true)**:

When enabled, the application queries CUPS for:
- Available printers (`conn.getPrinters()`)
- Default printer (`conn.getDefault()`)
- Media sizes per printer (`media-supported` attribute)
- Default media size (`media-default` attribute)
- Media dimensions (`media-size-supported` attribute)
- Printer resolution (`printer-resolution-default` attribute)

Configuration values act as fallbacks if CUPS queries fail.

**Static Mode (false)**:

When disabled, the application uses only these configuration values:
- `PRINTER.PRINTER` for default printer name
- `PRINTER.LABEL_SIZES` for available media sizes
- `LABEL.DEFAULT_SIZE` for default media
- `PRINTER.LABEL_PRINTABLE_AREA` for media dimensions

CUPS is still used for actual print jobs but not for discovering printers or media.

**Examples**:

Dynamic mode (recommended):
```json
{
  "PRINTER": {
    "USE_CUPS": true,
    "SERVER": "cups.local"
  }
}
```

Static mode (backward compatibility):
```json
{
  "PRINTER": {
    "USE_CUPS": false,
    "SERVER": "192.168.1.176",
    "PRINTER": "Zebra-LP2844",
    "LABEL_SIZES": {
      "Custom.4x6in": "4\" x 6\"",
      "Custom.3x1in": "3\" x 1\""
    },
    "LABEL_PRINTABLE_AREA": {
      "Custom.4x6in": [812, 1218],
      "Custom.3x1in": [609, 203]
    }
  }
}
```

**Usage Note**: 
- Use `true` for most deployments. Use `false` only for legacy configurations or when you need complete control over available media sizes.
- If CUPS server is unreachable and `USE_CUPS` is `true`, the application falls back to configuration values
- With `USE_CUPS: true`, custom sizes from `LABEL_SIZES` are merged with CUPS-reported sizes
- With `USE_CUPS: false`, **only** configuration sizes are available; CUPS sizes are ignored
- Settings page always queries CUPS for validation regardless of this flag



---

### PRINTER.SERVER

**Type**: `string`

**Description**: The hostname or IP address of the CUPS server. Can optionally include a port number. This is the server that will be queried for printer information and used for print jobs.

**Required**: Yes (for printing functionality)

**Default**: `"localhost"`

**Valid Values**:
- Hostname: `"cups.local"`, `"printserver"`, `"localhost"`
- IP address: `"192.168.1.176"`, `"10.0.0.50"`
- With port: `"cups.local:631"`, `"192.168.1.176:631"`
- `"localhost"` - Use local CUPS instance

**Examples**:

Local CUPS server:
```json
{
  "PRINTER": {
    "SERVER": "localhost"
  }
}
```

Remote CUPS server by IP:
```json
{
  "PRINTER": {
    "SERVER": "192.168.1.176"
  }
}
```

Remote CUPS with custom port:
```json
{
  "PRINTER": {
    "SERVER": "cups.local:631"
  }
}
```

**Usage Notes**:
- If port is not specified, CUPS uses its default port 631
- If server is unreachable, initialization errors are logged but startup continues
- DNS resolution failures are logged as connection errors
- Firewall restrictions on port 631 will cause connection failures
- In Docker, `localhost` refers to the container's localhost, not the host machine unless in `host` network mode
  - Use `host.docker.internal` on Docker Desktop to access host's CUPS
  - Use the host's IP address on Linux Docker
- Empty string defaults to `"localhost"`

**Validation**: The Settings page includes a "Validate" button that tests connectivity to this server.

---

### PRINTER.PRINTER

**Type**: `string`

**Description**: The name of the default printer to use. 
This printer will be pre-selected in the UI dropdowns. 
If empty and `USE_CUPS` is `true`, the CUPS default printer is used.

**Required**: 
- **Required** if `USE_CUPS: false`
- **Optional** if `USE_CUPS: true` (CUPS default will be used if empty)

**Default**: `""` (empty string)

**Valid Values**:
- Any printer name exactly as it appears in CUPS (case-sensitive)
- `""` (empty string) - Use CUPS default printer

**Examples**:

With explicit printer:
```json
{
  "PRINTER": {
    "PRINTER": "Zebra-LP2844"
  }
}
```

Use CUPS default:
```json
{
  "PRINTER": {
    "PRINTER": ""
  }
}
```

**Usage Notes**:
- If printer name doesn't match any available printer, validation warns but doesn't fail
- Users can still override via query parameter `?printer=OtherPrinter`
- When `USE_CUPS: false` and `PRINTER` is empty, print jobs will use the default CUPS printer if available; otherwise, printing fails
- When `USE_CUPS: true` and `PRINTER` is empty:
  - CUPS default printer is used if available (`conn.getDefault()`)
  - If no CUPS default exists, the first available printer is used
  - If no printers exist, validation shows an error
- Printer name is case-sensitive and must match CUPS name exactly
- If configured printer is in `PRINTERS_EXCLUDE` list, it won't appear in UI but direct API calls can still use it

**Priority**: See [Printer Selection Priority](#printer-selection-priority) for how this interacts with other settings.

---

### PRINTER.LABEL_SIZES

**Type**: `object` (dictionary) or `array` (list of tuples)

**Description**: Defines available label/media sizes and their human-readable names. Behavior depends on `USE_CUPS` setting:
- With `USE_CUPS: true` - Custom sizes to supplement CUPS media (merged with CUPS sizes)
- With `USE_CUPS: false` - The complete list of available sizes (CUPS media is ignored)

**Required**: 
- **Required** if `USE_CUPS: false`
- **Optional** if `USE_CUPS: true` (CUPS provides sizes; this supplements them)

**Default**: `{}` (empty dictionary) or `[]` (empty array)

**Valid Formats**:

**Dictionary format (recommended)**:
```json
{
  "LABEL_SIZES": {
    "sizeKey": "Human Readable Name",
    "4x6": "4\" x 6\"",
    "62mm": "62mm Label",
    "Custom.100x50mm": "Custom 100x50mm"
  }
}
```

**Array format (legacy compatibility)**:
```json
{
  "LABEL_SIZES": [
    ["sizeKey", "Human Readable Name"],
    ["4x6", "4\" x 6\""],
    ["62mm", "62mm Label"]
  ]
}
```

**Examples**:

Static configuration (USE_CUPS: false):
```json
{
  "PRINTER": {
    "USE_CUPS": false,
    "LABEL_SIZES": {
      "4x6": "4\" x 6\" Shipping Label",
      "3x1": "3\" x 1\" Address Label",
      "2.25x1.25": "2.25\" x 1.25\" Product Label"
    }
  }
}
```

Custom sizes with CUPS (USE_CUPS: true):
```json
{
  "PRINTER": {
    "USE_CUPS": true,
    "LABEL_SIZES": {
      "custom-large": "Custom 5\" x 8\" Label",
      "custom-small": "Custom 2\" x 3\" Label"
    }
  }
}
```

**Usage Notes**:
- With `USE_CUPS: true`:
  - CUPS sizes and custom sizes are merged
  - CUPS sizes take precedence if there's a key collision
  - Custom sizes are converted to CUPS format (`Custom.WxHmm`) using `LABEL_PRINTABLE_AREA` dimensions
  - If conversion fails, the original key is used
- With `USE_CUPS: false`:
  - Only these sizes are available; CUPS media is completely ignored
  - Each size key must have corresponding dimensions in `LABEL_PRINTABLE_AREA`
  - Missing dimensions for a size will cause printing to use default dimensions (300x200 pixels)
- Empty or missing `LABEL_SIZES` with `USE_CUPS: false` results in no available media
- Array format is automatically converted to dictionary internally
- Invalid entries (i.e. those that are not 2-element arrays or dictionary elements) are skipped with a warning
- Size keys are case-sensitive
- Sizes can be filtered per-printer using `ENABLED_SIZES`

**CUPS Media Format**: CUPS uses specific media name formats like `na_index-4x6_4x6in` or `Custom.100x50mm`. 
When `USE_CUPS: true`, the application handles conversion between config keys and CUPS formats automatically.

---

### PRINTER.LABEL_PRINTABLE_AREA

**Type**: `object` (dictionary mapping size keys to `[width, height]` arrays)

**Description**: Defines the printable dimensions in pixels for each label size. Used to calculate label dimensions 
and convert custom sizes to CUPS format.

**Required**:
- **Required** for all sizes in `LABEL_SIZES`
- **Optional** for all media retrieved via `USE_CUPS: true` (CUPS provides dimensions; this is fallback/override)

**Default**: `{}` (empty dictionary)

**Format**:
```json
{
  "LABEL_PRINTABLE_AREA": {
    "sizeKey": [widthInPixels, heightInPixels],
    "4x6": [812, 1218],
    "62mm": [437, 271]
  }
}
```

**Examples**:

Static configuration:
```json
{
  "PRINTER": {
    "USE_CUPS": false,
    "LABEL_SIZES": {
      "4x6": "4\" x 6\"",
      "3x1": "3\" x 1\""
    },
    "LABEL_PRINTABLE_AREA": {
      "4x6": [812, 1218],
      "3x1": [609, 203]
    }
  }
}
```

Custom size dimensions for CUPS:
```json
{
  "PRINTER": {
    "USE_CUPS": true,
    "LABEL_SIZES": {
      "custom": "Custom 5x3 Label"
    },
    "LABEL_PRINTABLE_AREA": {
      "custom": [1015, 609]
    }
  }
}
```

**Usage Notes**:
- With `USE_CUPS: true`:
  - CUPS `media-size-supported` attribute provides dimensions automatically
  - This setting acts as fallback if CUPS query fails
  - Custom sizes need dimensions here to calculate CUPS format (`Custom.WxHmm`)
  - DPI is queried from CUPS for conversion calculations
- With `USE_CUPS: false`:
  - **Must** include dimensions for every size in `LABEL_SIZES`
  - Missing dimensions result in default size (300x200 pixels)
  - DPI defaults to 203 if not calculable
- Dimensions must be positive integers
- Width and height are in pixels, not physical units
- Physical size calculation: `size_inches = pixels / printer_dpi`
- Invalid dimensions (negative, zero, non-numeric) may cause rendering errors
- Extremely large dimensions may cause memory issues or rendering failures

**Calculation Notes**:
- Standard thermal printer DPI: 203 (8 dots/mm)
- High-res thermal printer DPI: 300
- To calculate pixels: `pixels = physical_size_inches * dpi`
  - Example: 4" × 203 DPI = 812 pixels

---

### PRINTER.ENABLED_SIZES

**Type**: `object` (dictionary mapping printer names to arrays of size keys)

**Description**: Restricts which media sizes are available for specific printers. 
If a printer is not in this mapping, all sizes are available for it. 
This is useful when different printers support different media types.

**Required**: No

**Default**: `{}` (empty dictionary - no filtering, all sizes available for all printers)

**Format**:
```json
{
  "ENABLED_SIZES": {
    "PrinterName": ["sizeKey1", "sizeKey2"],
    "Zebra-LP2844": ["4x6", "3x1"],
    "Brother-QL-500": ["62mm", "29mm"]
  }
}
```

**Examples**:

Restrict sizes per printer:
```json
{
  "PRINTER": {
    "LABEL_SIZES": {
      "4x6": "4\" x 6\"",
      "3x1": "3\" x 1\"",
      "62mm": "62mm",
      "29mm": "29mm"
    },
    "ENABLED_SIZES": {
      "Zebra-LP2844": ["4x6", "3x1"],
      "Brother-QL-820NWB": ["62mm", "29mm"]
    }
  }
}
```

Allow all sizes for one printer, restrict another:
```json
{
  "PRINTER": {
    "ENABLED_SIZES": {
      "Office-Printer": ["4x6"]
    }
  }
}
```

**Usage Notes**:
- Useful in environments with multiple printers loaded with different media.
- Printers not in `ENABLED_SIZES` have access to all available sizes
- Empty array for a printer means no sizes are available (effectively disables printing)
- Size keys must match keys in `LABEL_SIZES` or CUPS media names (case-sensitive)
- If a printer's enabled sizes list contains invalid keys, those keys are ignored
- Works with both CUPS sizes and config-defined sizes
- Applied after CUPS query and custom size merging
- If `DEFAULT_SIZE` is not in the enabled list for the default printer, first enabled size is used
- Filtering happens in the UI and API; direct CUPS printing might bypass this

---

### PRINTER.PRINTERS_INCLUDE

**Type**: `array` (list of printer names)

**Description**: Whitelist of printers to show in the UI. If specified, **only** these printers will be available (subject to exclusion list). 
Empty or absent means all printers are included (subject to exclusion list).

**Required**: No

**Default**: `[]` (empty array - include all printers)

**Format**:
```json
{
  "PRINTERS_INCLUDE": ["PrinterName1", "PrinterName2"]
}
```

**Examples**:

Only show specific printers:
```json
{
  "PRINTER": {
    "PRINTERS_INCLUDE": ["Zebra-LP2844", "Brother-QL-820NWB"]
  }
}
```

Show all printers (default):
```json
{
  "PRINTER": {
    "PRINTERS_INCLUDE": []
  }
}
```

**Usage Notes**:
- If list contains printer names that don't exist, they're ignored
- If list excludes all available printers, no printers are shown (validation error)
- Case-sensitive matching against CUPS printer names
- Works with both CUPS-discovered printers and config-defined printers
- Applied before `PRINTERS_EXCLUDE`
- If configured `PRINTER.PRINTER` is not in include list, it won't be the default (first included printer used instead)
- Direct API calls with `?printer=Name` can potentially bypass this filter

**Filter Order**: Include filter is applied first, then exclude filter.

---

### PRINTER.PRINTERS_EXCLUDE

**Type**: `array` (list of printer names)

**Description**: Blacklist of printers to hide from the UI. These printers will not appear in printer selection dropdowns. 
Applied after `PRINTERS_INCLUDE` filter, so they will be hidden even if in the included filter.

**Required**: No

**Default**: `[]` (empty array - don't exclude any printers)

**Format**:
```json
{
  "PRINTERS_EXCLUDE": ["PrinterName1", "PrinterName2"]
}
```

**Examples**:

Hide specific printers:
```json
{
  "PRINTER": {
    "PRINTERS_EXCLUDE": ["Office-Color-Printer", "PDF-Printer"]
  }
}
```

Combined with include list:
```json
{
  "PRINTER": {
    "PRINTERS_INCLUDE": ["Zebra-LP2844", "Brother-QL-500", "Office-Printer"],
    "PRINTERS_EXCLUDE": ["Office-Printer"]
  }
}
```
Result: Only Zebra and Brother printers are shown.

**Usage Notes**:
- If printer is in both include and exclude lists, exclude takes precedence (printer is hidden)
- If all remaining printers are excluded, validation shows error
- Case-sensitive matching
- If configured `PRINTER.PRINTER` is in exclude list, it won't be the default (first available printer used instead)
- Direct API calls with `?printer=Name` can potentially bypass this filter

**Filter Order**: Include filter first, then exclude filter.

---

## LABEL Section

Controls default values for label rendering, including size, orientation, fonts, and font size.
These are the defaults used on the label designer UI and API unless overridden.

### LABEL.DEFAULT_SIZE

**Type**: `string`

**Description**: The default media size key to pre-select in the UI. Must match a key from `LABEL_SIZES` or a CUPS media name.

**Required**: No

**Default**: `""` (empty - use printer's default or first available size)

**Valid Values**:
- Any key from `PRINTER.LABEL_SIZES` (when `USE_CUPS: false`)
- Any CUPS media name (when `USE_CUPS: true`)
- `""` (empty string) - Use automatic default

**Examples**:

Specific default size:
```json
{
  "LABEL": {
    "DEFAULT_SIZE": "4x6"
  }
}
```

Use automatic default:
```json
{
  "LABEL": {
    "DEFAULT_SIZE": ""
  }
}
```

**Usage Notes**:
- With `USE_CUPS: true`:
  - If empty, CUPS `media-default` attribute is used
  - If CUPS doesn't provide a default, first available size is used
  - If specified key doesn't match any CUPS or config size, validation warns
- With `USE_CUPS: false`:
  - If empty, first size in `LABEL_SIZES` is used
  - Must match a key in `LABEL_SIZES` exactly (case-sensitive)
- If specified size is not in the enabled sizes for the default printer (`ENABLED_SIZES`), it may not be used
- Query parameter `?label_size=key` overrides this default
- One default is set globally. If the printer does not have that size enabled, the CUPS default for that printer, or the first available size for that printer is used instead.

**Priority**: See [Default Media Selection Priority](#default-media-selection-priority).

---

### LABEL.DEFAULT_ORIENTATION

**Type**: `string`

**Description**: The default label orientation for rendering. Controls whether text and elements are rendered in standard (horizontal) or rotated (vertical) orientation.

**Required**: No

**Default**: `"standard"`

**Valid Values**:
- `"standard"` - Horizontal/landscape orientation
- `"rotated"` - Vertical/portrait orientation (90° rotation)

**Examples**:

Standard orientation:
```json
{
  "LABEL": {
    "DEFAULT_ORIENTATION": "standard"
  }
}
```

Rotated orientation:
```json
{
  "LABEL": {
    "DEFAULT_ORIENTATION": "rotated"
  }
}
```

**Usage Notes**:
- Invalid values default to `"standard"`
- Case-sensitive (lowercase only)
- This is a default that can be overridden via UI or API parameter
- Orientation affects text positioning and margin calculations
- Does not physically rotate the label; only affects how content is laid out

---

### LABEL.DEFAULT_FONT_SIZE

**Type**: `integer`

**Description**: The default font size in points for text elements that don't specify their own size.

**Required**: No

**Default**: `70`

**Valid Values**: Any positive integer (typical range: 8-200)

**Examples**:

Default font size:
```json
{
  "LABEL": {
    "DEFAULT_FONT_SIZE": 70
  }
}
```

Smaller labels:
```json
{
  "LABEL": {
    "DEFAULT_FONT_SIZE": 40
  }
}
```

**Corner Cases**:
- Must be a positive integer
- Values less than 1 may cause rendering errors
- Very large values (>500) may exceed label dimensions
- As this is a default; templates and API calls can override per-element
- Affects margin calculations on the labeldesigner page (margins are expressed as percentages of font size)
- Different templates may have their own font size specifications

---

### LABEL.DEFAULT_FONTS

**Type**: `object` (single font) or `array` (list of font fallbacks)

**Description**: The default font(s) to use for text rendering. Can specify a single font or a list of fonts to try in order (fallback chain). Each font consists of a `family` and `style`.

**Required**: No

**Default**: `{"family": "DejaVu Sans", "style": "Book"}`

**Format**:

**Single font (object)**:
```json
{
  "DEFAULT_FONTS": {
    "family": "Font Family Name",
    "style": "Font Style"
  }
}
```

**Multiple fonts with fallback (array)**:
```json
{
  "DEFAULT_FONTS": [
    {"family": "Preferred Font", "style": "Bold"},
    {"family": "Fallback Font", "style": "Regular"},
    {"family": "Last Resort", "style": "Book"}
  ]
}
```

**Examples**:

Single font:
```json
{
  "LABEL": {
    "DEFAULT_FONTS": {
      "family": "DejaVu Sans",
      "style": "Book"
    }
  }
}
```

Fallback chain:
```json
{
  "LABEL": {
    "DEFAULT_FONTS": [
      {"family": "Minion Pro", "style": "Semibold"},
      {"family": "Linux Libertine", "style": "Regular"},
      {"family": "DejaVu Serif", "style": "Book"}
    ]
  }
}
```

**Usage Notes**:
- If a font family doesn't exist, the next font in the list is tried
- If no fonts in the list are available, system default font is used
- Font family names are case-sensitive
- Font styles are case-sensitive and must match exactly (e.g., "Book", "Regular", "Bold", "Italic")
- Array format is converted internally; first available font is used
- Empty or malformed font specifications fall back to system default
- Additional fonts from `ADDITIONAL_FONT_FOLDER` are included in the search
- Font discovery happens at startup; new fonts require restart
- Validation checks if configured fonts are available and warns if not found
- Templates can override fonts per-element

**Common Font Families** (depends on system installation):
- DejaVu Sans, DejaVu Serif, DejaVu Sans Mono
- Liberation Sans, Liberation Serif, Liberation Mono

**Common Font Styles**:
- Book, Regular, Roman (normal weight)
- Bold, Semibold
- Italic, Oblique
- Bold Italic

---

## WEBSITE Section

Controls the text displayed in the web interface for branding and customization.

### WEBSITE.HTML_TITLE

**Type**: `string`

**Description**: The text displayed in the browser tab/window title. This is the `<title>` HTML element content.

**Required**: No

**Default**: `"Label Designer"`

**Valid Values**: Any string

**Examples**:

```json
{
  "WEBSITE": {
    "HTML_TITLE": "Label Designer"
  }
}
```

```json
{
  "WEBSITE": {
    "HTML_TITLE": "Acme Corp Label Printer"
  }
}
```

**Usage Notes**:
- HTML special characters should be avoided or properly escaped
- Very long titles may be truncated by browsers
- Empty string results in blank browser title
- Does not affect functionality, only UI appearance

---

### WEBSITE.PAGE_TITLE

**Type**: `string`

**Description**: The heading text displayed in the navigation bar at the top of every page.

**Required**: No

**Default**: `"Label Designer"`

**Valid Values**: Any string

**Examples**:

```json
{
  "WEBSITE": {
    "PAGE_TITLE": "Label Designer"
  }
}
```

```json
{
  "WEBSITE": {
    "PAGE_TITLE": "Warehouse Label System"
  }
}
```

**Usage Notes**:
- HTML is not interpreted; displayed as plain text
- Very long titles may affect navbar layout on mobile devices
- Empty string hides the title but navbar remains
- Does not affect functionality, only UI appearance

---

### WEBSITE.PAGE_HEADLINE

**Type**: `string`

**Description**: The subtitle or tagline text displayed prominently on the home/label designer page.

**Required**: No

**Default**: `"Design and print labels"`

**Valid Values**: Any string

**Examples**:

```json
{
  "WEBSITE": {
    "PAGE_HEADLINE": "Design and print labels"
  }
}
```

```json
{
  "WEBSITE": {
    "PAGE_HEADLINE": "Create professional shipping labels quickly"
  }
}
```

**Usage Notes**:
- HTML is not interpreted; displayed as plain text
- Empty string hides the headline
- Line breaks (`\n`) are not supported; text displays on one line
- Does not affect functionality, only UI appearance

---

## Configuration Priority and Fallbacks

The application uses a priority system when multiple sources can provide the same information. Understanding these priorities is crucial for predictable behavior.

### Printer Selection Priority

When determining which printer to use for a print job:

1. **Query parameter**: `?printer=PrinterName` (highest priority)
2. **PRINTER.PRINTER**: Configured default printer
3. **CUPS default**: Result of `conn.getDefault()` (if `USE_CUPS: true`)
4. **First available**: First printer in the filtered list
5. **Error**: If no printers are available

**Note**: Filters (`PRINTERS_INCLUDE`, `PRINTERS_EXCLUDE`) are applied before selection.

### Media Size Priority

When determining available media sizes:

1. **USE_CUPS: true**:
   - CUPS `media-supported` attribute for the selected printer
   - Merged with `PRINTER.LABEL_SIZES` (custom sizes)
   - CUPS sizes take precedence on key collision
   - Fallback to `PRINTER.LABEL_SIZES` if CUPS query fails

2. **USE_CUPS: false**:
   - `PRINTER.LABEL_SIZES` exclusively
   - No CUPS metadata is used
   - Error if `LABEL_SIZES` is empty

**Filter**: `PRINTER.ENABLED_SIZES` is applied after size collection.

### Default Media Selection Priority

When determining the default/pre-selected media size:

1. **Query parameter**: `?label_size=key` (highest priority)
2. **CUPS default**: `media-default` attribute (if `USE_CUPS: true`)
3. **LABEL.DEFAULT_SIZE**: Configured default
4. **First available**: First size in the available list
5. **Error**: If no sizes are available

### Media Dimensions Priority

When determining the pixel dimensions of a media size:

1. **CUPS dimensions**: `media-size-supported` attribute with exact dimensions (if `USE_CUPS: true`)
2. **Parse from name**: Extract dimensions from media name (e.g., "4x6in" → 812x1218 pixels @ 203 DPI)
3. **PRINTER.LABEL_PRINTABLE_AREA**: Configured dimensions
4. **Default**: (300, 200) pixels as last resort

**Note**: DPI for calculations is obtained from CUPS `printer-resolution-default` or defaults to 203.

---

## Corner Cases and Special Behaviors

### Empty or Missing Default Printer

**Scenario**: `PRINTER.PRINTER` is empty or not specified.

**Behavior**:
- With `USE_CUPS: true`:
  - Application attempts to use CUPS default printer (`conn.getDefault()`)
  - If no CUPS default exists, uses first available printer from `conn.getPrinters()`
  - If no printers exist, validation shows error but startup continues
- With `USE_CUPS: false`:
  - Print operations will fail
  - Validation shows error

**Resolution**: Either configure a default printer or ensure CUPS has a default printer set.

**Important**: An empty `PRINTER.PRINTER` with available CUPS printers is **valid**.

---

### CUPS Server Connection Failures

**Scenario**: Configured CUPS server is unreachable or not responding.

**Behavior**:
- Initialization errors are logged to the console
- Initialization errors are stored in `instance.initialization_errors[]`
- Validation shows these errors in the UI
- Application continues to run (doesn't crash)
- With `USE_CUPS: true`: Falls back to configuration values where possible
- Settings page validation will show connection errors

**Common Causes**:
- CUPS server not running
- Incorrect `PRINTER.SERVER` address
- Firewall blocking port 631
- Network connectivity issues
- In Docker: `localhost` refers to container, not host

**Resolution**: Fix connectivity issues and reload configuration or restart application.

---

### Custom Media Sizes with CUPS

**Scenario**: Using custom media sizes not defined in CUPS when `USE_CUPS: true`.

**Behavior**:
1. Custom sizes are defined in `LABEL_SIZES` and `LABEL_PRINTABLE_AREA`
2. Application converts size keys to CUPS format (e.g., `Custom.100x50mm`)
3. Conversion uses printer DPI from CUPS and configured pixel dimensions
4. Converted CUPS name is sent with print job
5. CUPS accepts custom media if printer supports it

**Example**:
```json
{
  "PRINTER": {
    "USE_CUPS": true,
    "LABEL_SIZES": {
      "my-custom": "My Custom 5x3 Label"
    },
    "LABEL_PRINTABLE_AREA": {
      "my-custom": [1015, 609]
    }
  }
}
```

Internally converted to `Custom.127x76mm` for CUPS (at 203 DPI).

**Limitations**:
- Printer must support custom media sizes
- CUPS must be configured to allow custom sizes
- Incorrect dimensions may result in print errors

---

### Font Fallback Behavior

**Scenario**: Configured font is not available on the system.

**Behavior**:
1. If `DEFAULT_FONTS` is an array, try each font in order
2. If font family not found, skip to next font in list
3. If font family exists but style doesn't match, use first available style for that family
4. If no configured fonts are available, use system default font
5. Validation warnings are shown but don't prevent operation

**Example**:
```json
{
  "LABEL": {
    "DEFAULT_FONTS": [
      {"family": "CustomFont", "style": "Bold"},
      {"family": "Arial", "style": "Regular"},
      {"family": "DejaVu Sans", "style": "Book"}
    ]
  }
}
```

If CustomFont is not installed, Arial is tried. If Arial is not available, DejaVu Sans is used.

---

### Empty Configuration Sections

**Scenario**: Configuration file is missing entire sections.

**Behavior**:
- Missing `SERVER` section: Uses all defaults (host 0.0.0.0, port 8013, etc.)
- Missing `PRINTER` section: Initialization error logged, may fail to print
- Missing `LABEL` section: Uses all defaults
- Missing `WEBSITE` section: Uses default branding

**Example minimal valid config**:
```json
{
  "PRINTER": {
    "SERVER": "localhost"
  }
}
```

All other sections use defaults.

---

### LABEL_SIZES Format Compatibility

**Scenario**: Config contains `LABEL_SIZES` in array format (legacy).

**Behavior**:
- Array format: `[["key1", "label1"], ["key2", "label2"]]`
- Automatically converted to dictionary: `{"key1": "label1", "key2": "label2"}`
- Conversion happens internally; both formats are equivalent
- Invalid array entries (not 2 elements) are skipped with warning

**Recommendation**: Use dictionary format for new configurations.

---

### Initialization Errors

**Scenario**: Errors occur during CUPS initialization.

**Behavior**:
- Errors are collected in `instance.initialization_errors[]`
- Logged to console with ERROR level
- Settings page validation includes these errors
- Application continues to run (doesn't crash on CUPS errors)
- Errors are cleared and recalculated on reinitialization

**Common Errors**:
- "Failed to retrieve printer data from CUPS server" - Connection failure
- "No printer configuration found in config file" - Missing PRINTER section
- "Error getting list of printers from CUPS server" - CUPS query failure

**Access**: View initialization errors in Settings → Validate Config.

---

### Configuration File Not Found

**Scenario**: No configuration file exists at expected paths.

**Behavior**:
1. Try `/appconfig/config.json`
2. Try `config.json` in current directory
3. Try `config.minimal.json`
4. If all fail: Use built-in defaults and log warning
5. Warning added to `CONFIG_ERRORS[]`
6. Application continues with defaults
7. Settings page shows warning and allows configuration creation

**Warning Message**: "Warning: No config file found. Using default configuration. Please configure settings on the settings page."

---

### Invalid JSON in Configuration

**Scenario**: Configuration file exists but contains invalid JSON.

**Behavior**:
- JSON parsing error is caught
- Error message added to `CONFIG_ERRORS[]`
- Application uses built-in defaults
- Error logged to console
- Settings page shows the parse error

**Example Error**: "Error: Failed to parse config file: Expecting ',' delimiter: line 5 column 3 (char 89)"

**Resolution**: Fix JSON syntax errors or recreate config using Settings page.

---

## Complete Configuration Examples

### Minimal CUPS Configuration

Small, valid configuration for dynamic CUPS mode:

```json
{
  "SERVER": {
    "HOST": "0.0.0.0",
    "LOGLEVEL": "INFO"
  },
  "PRINTER": {
    "USE_CUPS": true,
    "SERVER": "localhost"
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

**What's provided by CUPS**:
- Available printers
- Default printer
- Media sizes
- Default media
- Media dimensions
- Printer resolution

---

### Full Static Configuration

Complete configuration for static mode without CUPS queries:

```json
{
  "SERVER": {
    "HOST": "0.0.0.0",
    "PORT": 8013,
    "LOGLEVEL": "INFO",
    "ADDITIONAL_FONT_FOLDER": "/fonts"
  },
  "PRINTER": {
    "USE_CUPS": false,
    "SERVER": "192.168.1.176",
    "PRINTER": "Zebra-LP2844",
    "LABEL_SIZES": {
      "4x6": "4\" x 6\" Shipping Label",
      "3x1": "3\" x 1\" Address Label",
      "2.25x1.25": "2.25\" x 1.25\" Product Label"
    },
    "LABEL_PRINTABLE_AREA": {
      "4x6": [812, 1218],
      "3x1": [609, 203],
      "2.25x1.25": [457, 254]
    },
    "ENABLED_SIZES": {},
    "PRINTERS_INCLUDE": [],
    "PRINTERS_EXCLUDE": []
  },
  "LABEL": {
    "DEFAULT_SIZE": "4x6",
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

---

### Hybrid Configuration

CUPS-enabled with custom sizes and filters:

```json
{
  "SERVER": {
    "HOST": "0.0.0.0",
    "LOGLEVEL": "WARNING",
    "ADDITIONAL_FONT_FOLDER": "/custom-fonts"
  },
  "PRINTER": {
    "USE_CUPS": true,
    "SERVER": "cups.local:631",
    "PRINTER": "Zebra-LP2844",
    "LABEL_SIZES": {
      "custom-large": "Custom 5\" x 8\"",
      "custom-small": "Custom 2\" x 3\""
    },
    "LABEL_PRINTABLE_AREA": {
      "custom-large": [1015, 1624],
      "custom-small": [406, 609]
    },
    "ENABLED_SIZES": {
      "Zebra-LP2844": ["4x6", "3x1", "custom-small"],
      "Brother-QL": ["62mm", "29mm"]
    },
    "PRINTERS_INCLUDE": ["Zebra-LP2844", "Brother-QL", "Office-Label"],
    "PRINTERS_EXCLUDE": ["Office-Color"]
  },
  "LABEL": {
    "DEFAULT_SIZE": "",
    "DEFAULT_ORIENTATION": "standard",
    "DEFAULT_FONT_SIZE": 60,
    "DEFAULT_FONTS": [
      {"family": "Arial", "style": "Bold"},
      {"family": "DejaVu Sans", "style": "Book"}
    ]
  },
  "WEBSITE": {
    "HTML_TITLE": "Warehouse Labels",
    "PAGE_TITLE": "Warehouse Label System",
    "PAGE_HEADLINE": "Print shipping and inventory labels"
  }
}
```

**Features**:
- Uses CUPS for discovery and metadata
- Adds two custom media sizes
- Restricts specific sizes to specific printers
- Filters printer list
- Font fallback chain

---

### Multi-Printer Configuration with Filters

Managing multiple printers with specific configurations:

```json
{
  "SERVER": {
    "HOST": "0.0.0.0",
    "LOGLEVEL": "INFO",
    "ADDITIONAL_FONT_FOLDER": false
  },
  "PRINTER": {
    "USE_CUPS": true,
    "SERVER": "192.168.1.100",
    "PRINTER": "Shipping-Labels",
    "ENABLED_SIZES": {
      "Shipping-Labels": ["4x6", "4x8"],
      "Product-Labels": ["2.25x1.25", "3x1"],
      "Address-Labels": ["3x1", "2x1"],
      "QA-Labels": ["2x2"]
    },
    "PRINTERS_INCLUDE": [
      "Shipping-Labels",
      "Product-Labels",
      "Address-Labels",
      "QA-Labels"
    ],
    "PRINTERS_EXCLUDE": [
      "Office-Printer",
      "Color-Printer",
      "PDF-Printer"
    ]
  },
  "LABEL": {
    "DEFAULT_SIZE": "",
    "DEFAULT_ORIENTATION": "standard",
    "DEFAULT_FONT_SIZE": 70,
    "DEFAULT_FONTS": [
      {"family": "Liberation Sans", "style": "Bold"}
    ]
  },
  "WEBSITE": {
    "HTML_TITLE": "Production Label System",
    "PAGE_TITLE": "Production Labels",
    "PAGE_HEADLINE": "Multi-department label printing"
  }
}
```

**Features**:
- Specific size restrictions per printer type
- Include list defines all authorized printers
- Exclude list removes unwanted printers
- Empty DEFAULT_SIZE uses each printer's CUPS default
