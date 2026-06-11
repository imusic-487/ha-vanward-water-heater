"""Switch entities for Vanward water heaters."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VanwardCoordinator
from .entity import VanwardEntity
from .protocol import VanwardDeviceState


@dataclass(frozen=True, slots=True)
class VanwardSwitchDescription:
    key: str
    translation_key: str
    value_fn: Callable[[VanwardDeviceState], bool]
    set_fn: Callable[[VanwardCoordinator, bool], Awaitable[None]]


SWITCHES = [
    VanwardSwitchDescription(
        "power",
        "power",
        lambda state: state.power,
        lambda coordinator, enabled: coordinator.client.async_set_power(
            coordinator.device_id, enabled
        ),
    ),
    VanwardSwitchDescription(
        "boost",
        "boost",
        lambda state: state.boost,
        lambda coordinator, enabled: coordinator.client.async_set_boost(
            coordinator.device_id, enabled
        ),
    ),
    VanwardSwitchDescription(
        "single_cruise",
        "single_cruise",
        lambda state: state.single_cruise,
        lambda coordinator, enabled: coordinator.client.async_set_single_cruise(
            coordinator.device_id, enabled
        ),
    ),
    VanwardSwitchDescription(
        "enjoy_cruise",
        "enjoy_cruise",
        lambda state: state.enjoy_cruise,
        lambda coordinator, enabled: coordinator.client.async_set_enjoy_cruise(
            coordinator.device_id, enabled
        ),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"].values()
    async_add_entities(
        VanwardSwitch(coordinator, description)
        for coordinator in coordinators
        for description in SWITCHES
    )


class VanwardSwitch(VanwardEntity, SwitchEntity):
    """Switch entity."""

    def __init__(
        self,
        coordinator: VanwardCoordinator,
        description: VanwardSwitchDescription,
    ) -> None:
        super().__init__(coordinator, description.key, description.translation_key)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs: object) -> None:
        await self.entity_description.set_fn(self.coordinator, True)

    async def async_turn_off(self, **kwargs: object) -> None:
        await self.entity_description.set_fn(self.coordinator, False)
