"""Select entities for Vanward water heaters."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import BATHROOM_MODE_OPTIONS, CRUISE_OPTIONS, DOMAIN
from .coordinator import VanwardCoordinator
from .entity import VanwardEntity
from .protocol import VanwardDeviceState

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class VanwardSelectDescription:
    key: str
    translation_key: str
    options: list[str]
    value_fn: Callable[[VanwardDeviceState], str | None]
    set_fn: Callable[[VanwardCoordinator, str], Awaitable[None]]
    translation_placeholders: dict[str, str] | None = None


SELECTS = [
    VanwardSelectDescription(
        "cruise_mode",
        "cruise_mode",
        CRUISE_OPTIONS,
        lambda state: state.cruise_mode,
        lambda coordinator, option: coordinator.client.async_set_cruise_mode(
            coordinator.device_id, option
        ),
    ),
    VanwardSelectDescription(
        "bathroom_mode",
        "bathroom_mode",
        BATHROOM_MODE_OPTIONS,
        lambda state: state.bathroom_mode,
        lambda coordinator, option: coordinator.client.async_set_bathroom_mode(
            coordinator.device_id, option
        ),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"].values()
    entities = [
        VanwardSelect(coordinator, description)
        for coordinator in coordinators
        for description in SELECTS
    ]
    _LOGGER.debug("Adding %s Vanward select entities", len(entities))
    async_add_entities(entities)


class VanwardSelect(VanwardEntity, SelectEntity):
    """Select entity."""

    def __init__(
        self,
        coordinator: VanwardCoordinator,
        description: VanwardSelectDescription,
    ) -> None:
        super().__init__(coordinator, description.key, description.translation_key)
        self.entity_description = description
        self._attr_options = description.options

    @property
    def current_option(self) -> str | None:
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_select_option(self, option: str) -> None:
        await self.entity_description.set_fn(self.coordinator, option)
