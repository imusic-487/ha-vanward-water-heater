"""Binary sensor entities for Vanward water heaters."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VanwardCoordinator
from .entity import VanwardEntity
from .protocol import VanwardDeviceState


@dataclass(frozen=True, slots=True)
class VanwardBinarySensorDescription:
    key: str
    translation_key: str
    value_fn: Callable[[VanwardDeviceState], bool]


BINARY_SENSORS = [
    VanwardBinarySensorDescription(
        "heating",
        "heating",
        lambda state: state.heating,
    ),
    VanwardBinarySensorDescription(
        "water_flowing",
        "water_flowing",
        lambda state: state.water_flowing,
    ),
    VanwardBinarySensorDescription(
        "fan",
        "fan",
        lambda state: state.fan,
    ),
    VanwardBinarySensorDescription(
        "antifreeze",
        "antifreeze",
        lambda state: state.antifreeze,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"].values()
    async_add_entities(
        VanwardBinarySensor(coordinator, description)
        for coordinator in coordinators
        for description in BINARY_SENSORS
    )


class VanwardBinarySensor(VanwardEntity, BinarySensorEntity):
    """Binary sensor entity."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(
        self,
        coordinator: VanwardCoordinator,
        description: VanwardBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key, description.translation_key)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        return self.entity_description.value_fn(self.coordinator.data)
