"""Sensor entities for Vanward water heaters."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VanwardCoordinator
from .entity import VanwardEntity
from .protocol import VanwardDeviceState


@dataclass(frozen=True, slots=True)
class VanwardSensorDescription:
    key: str
    translation_key: str
    device_class: SensorDeviceClass
    state_class: SensorStateClass
    unit: str
    value_fn: Callable[[VanwardDeviceState], float | None]


SENSORS = [
    VanwardSensorDescription(
        "current_water_usage",
        "current_water_usage",
        SensorDeviceClass.WATER,
        SensorStateClass.MEASUREMENT,
        "L",
        lambda state: state.current_water_usage,
    ),
    VanwardSensorDescription(
        "current_gas_usage",
        "current_gas_usage",
        SensorDeviceClass.GAS,
        SensorStateClass.MEASUREMENT,
        "m³",
        lambda state: state.current_gas_usage,
    ),
    VanwardSensorDescription(
        "total_water_usage",
        "total_water_usage",
        SensorDeviceClass.WATER,
        SensorStateClass.TOTAL,
        "L",
        lambda state: state.total_water_usage,
    ),
    VanwardSensorDescription(
        "total_gas_usage",
        "total_gas_usage",
        SensorDeviceClass.GAS,
        SensorStateClass.TOTAL,
        "m³",
        lambda state: state.total_gas_usage,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"].values()
    async_add_entities(
        VanwardSensor(coordinator, description)
        for coordinator in coordinators
        for description in SENSORS
    )


class VanwardSensor(VanwardEntity, SensorEntity):
    """Sensor entity."""

    def __init__(
        self,
        coordinator: VanwardCoordinator,
        description: VanwardSensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key, description.translation_key)
        self.entity_description = description
        self._attr_device_class = description.device_class
        self._attr_native_unit_of_measurement = description.unit
        self._attr_state_class = description.state_class

    @property
    def native_value(self) -> float | None:
        return self.entity_description.value_fn(self.coordinator.data)
