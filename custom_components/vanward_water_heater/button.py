"""Button entities for Vanward water heaters."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VanwardCoordinator
from .entity import VanwardEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"].values()
    entities = [VanwardCallButton(coordinator) for coordinator in coordinators]
    _LOGGER.debug("Adding %s Vanward button entities", len(entities))
    async_add_entities(entities)


class VanwardCallButton(VanwardEntity, ButtonEntity):
    """Call button entity."""

    def __init__(self, coordinator: VanwardCoordinator) -> None:
        super().__init__(coordinator, "call", "call")

    async def async_press(self) -> None:
        await self.coordinator.client.async_press_call(self.coordinator.device_id)
