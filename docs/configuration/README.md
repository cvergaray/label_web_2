# Configuration Documentation

This folder contains all configuration guidance for the application. Most users can configure everything through the UI, but manual JSON editing remains supported for advanced/legacy setups.

## How to Configure
- Open the app at `http://<host>:8013`, go to **Settings**, adjust values, and **Save All Settings**. This writes `config.json` for you.
- Use **Validate Config** and CUPS discovery features in the Settings page to verify connectivity and available printers/media before saving.
- Advanced users can still edit `config.json` directly (copy from `config.example.json` or `config.minimal.json`), then restart the app/container.

## Detailed Guides
- [ManualConfiguration](ManualConfiguration.md): Quick-start guide for minimal JSON configuration setup.
- [ConfigSections](ConfigSections.md): **Complete reference** with exhaustive detail on every configuration property, corner cases, and examples.
- [CustomSizes](CustomSizes.md): Guide for configuring custom label sizes for your printers.

## When to Use Which
- **Most users:** Configure via the Settings UI; no manual edits needed.
- **Need a quick manual JSON:** Start from [ManualConfiguration](ManualConfiguration.md) or `config.minimal.json`.
- **Need full detail/reference:** See [ConfigSections](ConfigSections.md) for exhaustive documentation of every configuration property.
- **Need custom label sizes:** See [CustomSizes](CustomSizes.md) for detailed instructions, although the settings UI can also help with this.

