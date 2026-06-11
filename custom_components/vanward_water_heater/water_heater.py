"""Water heater entity for Vanward water heaters."""

from __future__ import annotations

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, STATE_OFF, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import BATHROOM_MODE_OPTIONS, DOMAIN
from .coordinator import VanwardCoordinator
from .entity import VanwardEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"].values()
    async_add_entities(
        VanwardWaterHeater(coordinator) for coordinator in coordinators
    )


class VanwardWaterHeater(VanwardEntity, WaterHeaterEntity):
    """Water heater entity."""

    _attr_max_temp = 65
    _attr_min_temp = 30
    _attr_operation_list = [STATE_OFF, *BATHROOM_MODE_OPTIONS]
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
        | WaterHeaterEntityFeature.ON_OFF
    )
    _attr_target_temperature_step = 1
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: VanwardCoordinator) -> None:
        super().__init__(coordinator, "water_heater", "water_heater")

    @property
    def current_operation(self) -> str | None:
        state = self.coordinator.data
        if not state.power:
            return STATE_OFF
        return state.bathroom_mode

    @property
    def target_temperature(self) -> int:
        return self.coordinator.data.target_temperature

    async def async_set_temperature(self, **kwargs: object) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        await self.coordinator.client.async_set_target_temperature(
            self.coordinator.device_id, int(float(temperature))
        )

    async def async_turn_on(self) -> None:
        await self.coordinator.client.async_set_power(self.coordinator.device_id, True)

    async def async_turn_off(self) -> None:
        await self.coordinator.client.async_set_power(
            self.coordinator.device_id, False
        )

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        if operation_mode == STATE_OFF:
            await self.async_turn_off()
            return
        await self.async_turn_on()
        await self.coordinator.client.async_set_bathroom_mode(
            self.coordinator.device_id, operation_mode
        )
