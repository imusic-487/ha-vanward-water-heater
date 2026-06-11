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
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VanwardCoordinator
from .entity import VanwardEntity
from .protocol import VanwardDeviceState

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class VanwardSensorDescription(SensorEntityDescription):
    """Description for Vanward sensor entities."""

    value_fn: Callable[[VanwardDeviceState], float | None]


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


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinators = entry.runtime_data.coordinators.values()
    entities = [
        VanwardSensor(coordinator, description)
        for coordinator in coordinators
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
    def native_value(self) -> float | None:
        return self.entity_description.value_fn(self.coordinator.data)
