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

## HomeKit

After pairing via the HomeKit bridge (HASS Bridge), the heater appears as a **WaterHeater** accessory in the Home app — water temperature, target temperature and operation mode are all visible.

**Note**: the WaterHeater accessory carries its own current-temperature characteristic, so iOS Home shows it alongside other temperature devices under the "Temperature" category. This is normal HomeKit behavior, not a bug.

**To keep the water temperature out of the "ambient temperature" summary**:

1. Open the Home app → find the heater accessory
2. Long-press the tile → Settings (gear icon)
3. Turn off **"Include in Home Summaries"**

The water temperature on the heater's own tile is unaffected.

## Changelog

### 2026-08-12
- **Fix (no code change)**: water temperature appearing in the Home ambient-temperature summary is resolved by turning off **"Include in Home Summaries"** for the heater accessory in the iOS Home app (see the HomeKit section above)
- **Note**: an attempt to remove `device_class=temperature` from the cruise-temperature number entity in `number.py` was evaluated and reverted — that entity is not exposed to HomeKit (Number domain not in the include list), so the change had no practical effect and could affect other users relying on the classification; keeping upstream behavior
- **Docs**: README restructured to bilingual (Chinese primary + separate English file)

### 2026-08-11
- **Added**: electric water heater support (E60-Q2WY10-20) — auto-detects the 27-field status layout + reads current water temperature

## Disclaimer

This project is an unofficial community integration and is not affiliated with, endorsed by, or supported by Vanward. Use it at your own risk. Device behavior, cloud connectivity, and compatibility may change without notice.

## License

MIT
