"""Number entities for Vanward water heaters."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VanwardCoordinator
from .entity import VanwardEntity
from .protocol import VanwardDeviceState

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class VanwardNumberDescription:
    key: str
    translation_key: str
    minimum: int
    maximum: int
    value_fn: Callable[[VanwardDeviceState], int]
    set_fn: Callable[[VanwardCoordinator, int], Awaitable[None]]
    translation_placeholders: dict[str, str] | None = None


NUMBERS = [
    VanwardNumberDescription(
        "target_temperature",
        "target_temperature",
        30,
        65,
        lambda state: state.target_temperature,
        lambda coordinator, value: coordinator.client.async_set_target_temperature(
            coordinator.device_id, value
        ),
    ),
    VanwardNumberDescription(
        "cruise_temperature",
        "cruise_temperature",
        34,
        43,
        lambda state: state.cruise_temperature,
        lambda coordinator, value: coordinator.client.async_set_cruise_temperature(
            coordinator.device_id, value
        ),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"].values()
    entities = [
        VanwardNumber(coordinator, description)
        for coordinator in coordinators
        for description in NUMBERS
    ]
    _LOGGER.debug("Adding %s Vanward number entities", len(entities))
    async_add_entities(entities)


class VanwardNumber(VanwardEntity, NumberEntity):
    """Number entity."""

    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: VanwardCoordinator,
        description: VanwardNumberDescription,
    ) -> None:
        super().__init__(coordinator, description.key, description.translation_key)
        self.entity_description = description
        self._attr_native_min_value = description.minimum
        self._attr_native_max_value = description.maximum

    @property
    def native_value(self) -> int:
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_set_native_value(self, value: float) -> None:
        await self.entity_description.set_fn(self.coordinator, int(value))
