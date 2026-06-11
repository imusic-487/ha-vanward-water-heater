"""Constants for the Vanward water heater integration."""

from __future__ import annotations

DOMAIN = "vanward_water_heater"

CONF_MOBILE = "mobile"
CONF_DEVICE_IDS = "device_ids"

LOGIN_URL = "https://rubyapi.vanward.com/api/user/login"
WS_URL = "wss://rubyusercomet.vanward.com:2301/ws"

COMMAND_LOGIN = 0x00
COMMAND_UPDATE_STATUS = 0x04
COMMAND_HEARTBEAT = 0x0A
COMMAND_STATUS_REPORT = 0x22
COMMAND_HEARTBEAT_RESPONSE = 0x23

PLATFORMS = [
    "binary_sensor",
    "button",
    "number",
    "select",
    "sensor",
    "switch",
    "water_heater",
]

CRUISE_OPTIONS = ["关闭", "全天候", "点动", "预约", "自学习"]
BATHROOM_MODE_OPTIONS = ["普通", "自适温", "节能", "厨房洗", "儿童浴"]

BATHROOM_MODE_MAP = {
    1: ("普通", 45, 40),
    5: ("自适温", 45, 39),
    4: ("节能", 42, 38),
    2: ("厨房洗", 40, 36),
    24: ("儿童浴", 39, 35),
}

BATHROOM_MODE_BY_NAME = {
    name: (mode, temperature, cruise_temperature)
    for mode, (name, temperature, cruise_temperature) in BATHROOM_MODE_MAP.items()
}
