# Vanward Water Heater for Home Assistant

English | [简体中文](README.md)

> **Fork notice**: This repository is forked from [orangeboyChen/ha-vanward-water-heater](https://github.com/orangeboyChen/ha-vanward-water-heater). It keeps all original functionality and adds **electric water heater** support. Feedback and PRs are welcome.

A Home Assistant custom integration for Vanward water heaters. The original plugin mainly targets **gas** water heaters; this fork adds support for **electric** water heaters (e.g. E60-Q2WY10-20).

## Differences from upstream

### New: Electric water heater support
- `protocol.py`: auto-detects gas vs electric status layouts based on device type. Electric heaters only expose 27 status fields (no `gas_usage` / `water_flowing` / `fan` fields), which previously caused `ValueError: Status payload does not contain the expected fields`
- `water_heater.py`: exposes `current_temperature` for electric heaters
- Gas heater behavior is completely unchanged

**Tested on**: Home Assistant 2026.7.4 + Vanward E60-Q2WY10-20 (60L electric heater). Integration loads cleanly and water temperature reads correctly.

**Known limitations**:
- Only tested on E60-Q2WY10-20; other electric models (different capacities/newer revisions) are unverified
- Gas-specific entities (current water usage / current gas usage / total gas usage / total water usage) are still registered on electric heaters but stay at 0.0
- See upstream issue: [#1 Electric water heater (E60-Q2WY10-20) support proposal + patch](https://github.com/orangeboyChen/ha-vanward-water-heater/issues/1)

## Installation

Install this integration with HACS as a custom repository:

1. Open HACS in Home Assistant.
2. Go to `Integrations`.
3. Open the three-dot menu and choose `Custom repositories`.
4. Add this repository (use this fork if you need electric heater support):

```text
https://github.com/imusic-487/ha-vanward-water-heater
```

> Tip: for the original (gas-only) plugin, add `https://github.com/orangeboyChen/ha-vanward-water-heater`.

5. Select category `Integration`.
6. Install `Vanward Water Heater`.
7. Restart Home Assistant.

## Usage

After installation, go to:

```text
Settings -> Devices & services -> Add integration
```

Search for `Vanward Water Heater` and follow the setup flow.

## Disclaimer

This project is an unofficial community integration and is not affiliated with, endorsed by, or supported by Vanward. Use it at your own risk. Device behavior, cloud connectivity, and compatibility may change without notice.

## License

MIT
