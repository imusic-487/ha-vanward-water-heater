"""Protocol helpers ported from the Node-RED flow."""

from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Any

from .const import (
    BATHROOM_MODE_BY_NAME,
    BATHROOM_MODE_MAP,
    COMMAND_UPDATE_STATUS,
)


@dataclass(slots=True)
class VanwardDeviceInfo:
    """Static data required when sending status updates."""

    device_id: str
    model: str | None = None
    series: str | None = None
    name: str | None = None


@dataclass(slots=True)
class VanwardDeviceState:
    """Parsed water heater state."""

    raw_status: list[int]
    operational_status: list[int]
    device_info: VanwardDeviceInfo

    @property
    def power(self) -> bool:
        return bool(self.operational_status[0])

    @property
    def bathroom_mode(self) -> str | None:
        mode = self.operational_status[1]
        value = BATHROOM_MODE_MAP.get(mode)
        return value[0] if value else None

    @property
    def current_temperature(self) -> int:
        return self.raw_status[6]

    @property
    def target_temperature(self) -> int:
        return self.operational_status[2]

    @property
    def boost(self) -> bool:
        return _bit_enabled(self.operational_status[5], 2)

    @property
    def cruise_mode(self) -> str:
        cruise_flags = self.operational_status[5]
        booking_mode = self.operational_status[11]
        if booking_mode == 1:
            return "预约"
        if booking_mode == 2:
            return "自学习"
        if _bit_enabled(cruise_flags, 1):
            return "点动"
        if _bit_enabled(cruise_flags, 7):
            return "全天候"
        return "关闭"

    @property
    def cruise_temperature(self) -> int:
        return self.operational_status[6]

    @property
    def single_cruise(self) -> bool:
        return _bit_enabled(self.operational_status[5], 0)

    @property
    def enjoy_cruise(self) -> bool:
        return _bit_enabled(self.operational_status[5], 3)

    @property
    def current_water_usage(self) -> float | None:
        return _scale_status(self.raw_status, 11)

    @property
    def current_gas_usage(self) -> float | None:
        return _scale_status(self.raw_status, 17)

    @property
    def total_water_usage(self) -> float | None:
        return _scale_status(self.raw_status, 14)

    @property
    def total_gas_usage(self) -> float | None:
        return _scale_status(self.raw_status, 15)

    @property
    def heating(self) -> bool:
        return _raw_bit_enabled(self.raw_status, 8, 0x01)

    @property
    def water_flowing(self) -> bool:
        return _raw_bit_enabled(self.raw_status, 8, 0x02)

    @property
    def antifreeze(self) -> bool:
        return _raw_bit_enabled(self.raw_status, 8, 0x04)

    @property
    def fan(self) -> bool:
        return _raw_bit_enabled(self.raw_status, 8, 0x08)


def encode_message(command: int, payload: dict[str, Any] | None = None) -> bytes:
    """Encode a WebSocket frame using the flow's binary format."""

    body = b""
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    return bytes([command]) + len(body).to_bytes(4, "big") + body


def decode_message(message: bytes | bytearray) -> tuple[int, dict[str, Any]]:
    """Decode a WebSocket frame into command and JSON payload."""

    if len(message) < 5:
        raise ValueError("Message is shorter than the 5 byte header")
    command = message[0]
    length = int.from_bytes(message[1:5], "big")
    payload_bytes = bytes(message[5 : 5 + length])
    if not payload_bytes:
        return command, {}
    return command, json.loads(payload_bytes.decode())


def states_from_login_payload(payload: dict[str, Any]) -> dict[str, VanwardDeviceState]:
    """Build all device states returned by login."""

    devices = payload.get("data", {}).get("Devices") or payload.get("Devices") or []
    states: dict[str, VanwardDeviceState] = {}
    for device in devices:
        device_id = device.get("DeviceId")
        status = device.get("Status")
        if not device_id or not status:
            continue
        product = device.get("Product") or {}
        info = VanwardDeviceInfo(
            device_id=device_id,
            model=product.get("Model"),
            series=product.get("Series"),
            name=device.get("Name") or product.get("Name"),
        )
        states[device_id] = state_from_status(status, info)
    if not states:
        raise ValueError("No devices returned by the Vanward account")
    return states


def state_from_status(
    status: list[int], device_info: VanwardDeviceInfo
) -> VanwardDeviceState:
    """Convert the raw status list into the writable operational status list."""

    if len(status) <= 33:
        raise ValueError("Status payload does not contain the expected fields")

    operational_status = [
        status[1],
        status[2],
        status[6],
        status[25],
        status[4],
        status[18],
        status[19],
        status[20],
        status[21],
        0,
        0,
        status[33],
    ]
    return VanwardDeviceState(
        raw_status=status,
        operational_status=operational_status,
        device_info=device_info,
    )


def update_status_payload(state: VanwardDeviceState) -> tuple[int, dict[str, Any]]:
    """Create the update-status command payload."""

    info = state.device_info
    return (
        COMMAND_UPDATE_STATUS,
        {
            "Id": info.device_id,
            "MsgId": 1,
            "Model": info.model,
            "Series": info.series,
            "Status": state.operational_status,
            "Timestamp": int(time.time()),
        },
    )


def set_power(state: VanwardDeviceState, enabled: bool) -> bool:
    value = int(enabled)
    if state.operational_status[0] == value:
        return False
    state.operational_status[0] = value
    return True


def set_boost(state: VanwardDeviceState, enabled: bool) -> bool:
    return _set_status_bit(state, 2, enabled)


def set_target_temperature(state: VanwardDeviceState, temperature: int) -> bool:
    if state.operational_status[2] == temperature:
        return False
    state.operational_status[2] = temperature
    return True


def set_cruise_temperature(state: VanwardDeviceState, temperature: int) -> bool:
    if state.operational_status[6] == temperature:
        return False
    state.operational_status[6] = temperature
    return True


def set_single_cruise(state: VanwardDeviceState, enabled: bool) -> bool:
    changed = _set_status_bit(state, 0, enabled)
    if changed and enabled:
        state.operational_status[0] = 1
    return changed


def set_enjoy_cruise(state: VanwardDeviceState, enabled: bool) -> bool:
    return _set_status_bit(state, 3, enabled)


def set_cruise_mode(state: VanwardDeviceState, option: str) -> bool:
    if state.single_cruise:
        raise ValueError("Cruise mode cannot be changed while single cruise is enabled")

    before = list(state.operational_status)
    status = state.operational_status[5]
    if option == "预约":
        status = _replace_bit(status, 1, False)
        status = _replace_bit(status, 7, False)
        state.operational_status[5] = status
        state.operational_status[9] = 0
        state.operational_status[11] = 1
    elif option == "自学习":
        status = _replace_bit(status, 1, False)
        status = _replace_bit(status, 7, False)
        state.operational_status[5] = status
        state.operational_status[9] = 0
        state.operational_status[11] = 2
    elif option == "点动":
        status = _replace_bit(status, 1, True)
        status = _replace_bit(status, 7, False)
        state.operational_status[5] = status
        state.operational_status[9] = 0
        state.operational_status[11] = 0
    elif option == "全天候":
        status = _replace_bit(status, 1, False)
        status = _replace_bit(status, 7, True)
        state.operational_status[5] = status
        state.operational_status[9] = 0
        state.operational_status[11] = 0
    elif option == "关闭":
        status = _replace_bit(status, 1, False)
        status = _replace_bit(status, 7, False)
        state.operational_status[5] = status
        state.operational_status[9] = 0
        state.operational_status[11] = 0
    else:
        raise ValueError(f"Unsupported cruise mode: {option}")
    return before != state.operational_status


def set_bathroom_mode(state: VanwardDeviceState, option: str) -> bool:
    mode_data = BATHROOM_MODE_BY_NAME.get(option)
    if mode_data is None:
        raise ValueError(f"Unsupported bathroom mode: {option}")

    mode, temperature, cruise_temperature = mode_data
    if state.operational_status[1] == mode:
        return False
    state.operational_status[1] = mode
    state.operational_status[2] = temperature
    state.operational_status[6] = cruise_temperature
    return True


def press_call(state: VanwardDeviceState) -> bool:
    state.operational_status[10] = 8
    return True


def _scale_status(status: list[int], index: int) -> float | None:
    if len(status) <= index:
        return None
    return round(status[index] * 0.1, 1)


def _raw_bit_enabled(status: list[int], index: int, mask: int) -> bool:
    if len(status) <= index:
        return False
    return bool(status[index] & mask)


def _bit_enabled(value: int, index: int) -> bool:
    return f"{value:08b}"[index] == "1"


def _set_status_bit(state: VanwardDeviceState, bit_index: int, enabled: bool) -> bool:
    value = state.operational_status[5]
    updated = _replace_bit(value, bit_index, enabled)
    if value == updated:
        return False
    state.operational_status[5] = updated
    return True


def _replace_bit(value: int, index: int, enabled: bool) -> int:
    bits = list(f"{value:08b}")
    bits[index] = "1" if enabled else "0"
    return int("".join(bits), 2)
