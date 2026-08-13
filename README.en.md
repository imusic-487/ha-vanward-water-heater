# Vanward Water Heater for Home Assistant

English | [简体中文](README.md)

> **Fork notice**: This repository is forked from [orangeboyChen/ha-vanward-water-heater](https://github.com/orangeboyChen/ha-vanward-water-heater). It keeps all original functionality and adds **electric water heater** support. Feedback and PRs are welcome.

A Home Assistant custom integration for Vanward water heaters. The original plugin mainly targets **gas** water heaters; this fork adds support for **electric** water heaters (e.g. E60-Q2WY10-20).

## Differences from upstream

### New: Electric water heater support (v3.1)
- `protocol.py`: auto-detects gas vs electric status layouts based on device type. Electric heaters only expose 27 status fields (no `gas_usage` / `water_flowing` / `fan` fields), which previously caused `ValueError: Status payload does not contain the expected fields`
- **Electric mode code table**: Normal(1) / Medium-temp(2) / Anti-bacteria(10) / Capacity-boost(12) / ECO peak-off-peak(32) / e-push(35), mapped bidirectionally for read & write (e-push with auto-off flag reads back as 43, normalized to e-push for display)
- **Dual-track read/write**: electric layout writes mode to `Status[4]` and temperature to `Status[6]`, automatically distinguished from the gas layout (mode at `Status[1]`) — the two layouts never interfere
- **Temperature range**: 35–75°C for electric heaters (gas version: 30–65°C), adaptive per device type
- `water_heater.py`: exposes `current_temperature` for electric heaters
- **4 new electric sensors**: current water temperature / target temperature / current mode / power status
- **Feature bitmask**: flags like auto power-off are read/written bitwise with explanatory comments to avoid corrupting other bits
- **Device offline detection (v3.2)**: parses the `isOnline` field from the login payload (same source as the Vanward app's "设备离线" badge); when the device goes offline, entities automatically become `unavailable` and both HA and the HomeKit bridge show offline instead of stale cached state. Payloads without `isOnline` default to online to avoid false negatives
- Gas heater behavior is completely unchanged

**Tested on**: Home Assistant 2026.7.4 + Vanward E60-Q2WY10-20 (60L electric heater). Integration loads cleanly, water temperature reads correctly, all 6 entities work.

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

The 4 new electric sensors (current water temp / target temp / current mode / power status) appear automatically and can be used directly in dashboards, automations, or trend graphs.

## HomeKit

After pairing via the HomeKit bridge (HASS Bridge), the heater appears as a **WaterHeater** accessory in the Home app — water temperature, target temperature and operation mode are all visible.

**Notes**:
- The HomeKit protocol only exposes "Off / Heat" as heating states for water heaters (protocol limitation, not a plugin issue); modes like Anti-bacteria / ECO / e-push are selected in HA
- HomeKit control is **bidirectional**: changing the target temperature or switching the device in the Home app really does send the command to the heater
- The WaterHeater accessory carries its own current-temperature characteristic, so iOS Home shows it alongside other temperature devices under the "Temperature" category. This is normal HomeKit behavior, not a bug.

**To keep the water temperature out of the "ambient temperature" summary**:

1. Open the Home app → find the heater accessory
2. Long-press the tile → Settings (gear icon)
3. Turn off **"Include in Home Summaries"**

**Electric sensors & HomeKit**: the current-water-temp / target-temp sensors (sensor domain) are bridged to HomeKit as standalone temperature accessories by default; if not needed, add them to the bridge's `exclude_entities` list in the HomeKit bridge configuration.

## Changelog

### 2026-08-13
- **Added (v3.2)**: device offline detection — parses the `isOnline` flag from the login response (same source as the Vanward app's "设备离线" badge); entities automatically become `unavailable` when the device goes offline, so HA and the HomeKit bridge show offline instead of stale cached state. Payloads without the flag default to online to avoid false negatives
- **Added (v3.2)**: 4 offline-detection test cases (online / offline / missing-flag compatibility / default), test suite 33 → 37
- **Added (v3.1)**: electric mode code table (Normal/Medium/Anti-bacteria/Capacity-boost/ECO/e-push) with bidirectional read/write mapping; dual-track mode/temperature read-write (electric Status[4]/Status[6]); adaptive temperature range 35–75°C; feature bitmask read/write
- **Added (v3.1)**: 4 electric sensors — current water temperature / target temperature / current mode / power status
- **Fixed**: 3 CRITICAL + 3 MAJOR issues found in code review (mode read position, electric mode code table, ghost entity hiding, temperature range, e-push flag, missing tests)
- **HomeKit**: electric sensors are bridged as standalone temperature accessories by default; excludable via bridge config

### 2026-08-12
- **Fix (no code change)**: water temperature appearing in the Home ambient-temperature summary is resolved by turning off **"Include in Home Summaries"** for the heater accessory in the iOS Home app (see the HomeKit section above)
- **Note**: an attempt to remove `device_class=temperature` from the cruise-temperature number entity in `number.py` was evaluated and reverted — that entity is not exposed to HomeKit (Number domain not in the include list), so the change had no practical effect and could affect other users relying on the classification; keeping upstream behavior
- **Docs**: README restructured to bilingual (Chinese primary + separate English file)

### 2026-08-11
- **Added**: electric water heater support (E60-Q2WY10-20) — auto-detects the 27-field status layout + reads current water temperature

## Disclaimer

This project is an unofficial community integration and is not affiliated with, endorsed by, or supported by Vanward. It is implemented by analyzing the device's local communication protocol and contains no proprietary vendor code or assets. Use it at your own risk. Device behavior, cloud connectivity, and compatibility may change without notice.

## License

MIT
