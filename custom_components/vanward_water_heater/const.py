"""Constants for the Vanward water heater integration."""

from __future__ import annotations

from homeassistant.const import Platform

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
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.WATER_HEATER,
]

CRUISE_OPTIONS = ["关闭", "全天候", "点动", "预约", "自学习"]

# ── 燃气机型模式表（作者原版，原样保留）─────────────────────────────
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

# ── 电热机型模式表（Q2 系列，APK main.js 三路证据实锤 2026-08-13）──
# 模式码: 1普通 / 2中温 / 10抑菌 / 12增容 / 32ECO峰谷 / 35e-push
# e-push 带自动断电标志时写入 43（0b00100011 | bit4 = 0b00101011）
# 增容/ECO/e-push 实际目标温度由设备缓存（sendQ2 机制），表内温度仅为默认值
ELECTRIC_MODE_OPTIONS = ["普通", "中温", "抑菌", "增容", "ECO峰谷", "e-push"]

ELECTRIC_MODE_MAP = {
    1: ("普通", 45, 40),
    2: ("中温", 60, 60),
    10: ("抑菌", 45, 40),
    12: ("增容", 45, 40),
    32: ("ECO峰谷", 45, 40),
    35: ("e-push", 45, 40),
    # 43 = e-push 带自动断电标志时的读值（0b00101011），显示归一到 e-push
    43: ("e-push", 45, 40),
}

ELECTRIC_MODE_BY_NAME = {
    name: (mode, temperature, cruise_temperature)
    for mode, (name, temperature, cruise_temperature) in ELECTRIC_MODE_MAP.items()
    if mode != 43  # 43 仅读值归一化（e-push+自动断电标志），写入必须用 35
}

# 电热机型水温范围（E60-Q2WY10-20 产品资料）
ELECTRIC_MIN_TEMP = 35
ELECTRIC_MAX_TEMP = 75
