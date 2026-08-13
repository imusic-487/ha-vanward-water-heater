"""Sensor entities for Vanward water heaters."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VanwardCoordinator
from .entity import VanwardEntity
from .protocol import VanwardDeviceState

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class VanwardSensorDescription(SensorEntityDescription):
    """Description for Vanward sensor entities."""

    value_fn: Callable[[VanwardDeviceState], float | str | None]


# 燃气机型传感器（耗水耗气，原版保留）
SENSORS = [
    VanwardSensorDescription(
        key="current_water_usage",
        translation_key="current_water_usage",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        value_fn=lambda state: state.current_water_usage,
    ),
    VanwardSensorDescription(
        key="current_gas_usage",
        translation_key="current_gas_usage",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        value_fn=lambda state: state.current_gas_usage,
    ),
    VanwardSensorDescription(
        key="total_water_usage",
        translation_key="total_water_usage",
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        value_fn=lambda state: state.total_water_usage,
    ),
    VanwardSensorDescription(
        key="total_gas_usage",
        translation_key="total_gas_usage",
        device_class=SensorDeviceClass.GAS,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        value_fn=lambda state: state.total_gas_usage,
    ),
]

# 电热机型传感器（Q2 系列，2026-08-13 新增）
ELECTRIC_SENSORS = [
    VanwardSensorDescription(
        key="current_temperature",
        name="当前水温",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda state: state.current_temperature,
    ),
    VanwardSensorDescription(
        key="target_temperature",
        name="目标温度",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda state: state.target_temperature,
    ),
    VanwardSensorDescription(
        key="operation_mode",
        name="当前模式",
        value_fn=lambda state: state.bathroom_mode,
    ),
    VanwardSensorDescription(
        key="power",
        name="电源状态",
        value_fn=lambda state: "开" if state.power else "关",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    # C3：按机型分流——燃气注册耗水耗气，电热注册水温/目标/模式/电源
    electric = [
        c for c in entry.runtime_data.coordinators.values() if c.data.electric
    ]
    gas = [c for c in entry.runtime_data.coordinators.values() if not c.data.electric]
    entities = [
        VanwardSensor(coordinator, description)
        for coordinator in electric
        for description in ELECTRIC_SENSORS
    ] + [
        VanwardSensor(coordinator, description)
        for coordinator in gas
        for description in SENSORS
    ]
    _LOGGER.debug("Adding %s Vanward sensor entities", len(entities))
    async_add_entities(entities)


class VanwardSensor(VanwardEntity, SensorEntity):
    """Sensor entity."""

    def __init__(
        self,
        coordinator: VanwardCoordinator,
        description: VanwardSensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key, description.translation_key)
        self.entity_description = description

    @property
    def native_value(self) -> float | str | None:
        return self.entity_description.value_fn(self.coordinator.data)
