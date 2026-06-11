"""Data coordinator for Vanward water heaters."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import VanwardApiClient, VanwardAuthError, VanwardSessionExpired
from .const import DOMAIN
from .protocol import VanwardDeviceState

_LOGGER = logging.getLogger(__name__)


class VanwardCoordinator(DataUpdateCoordinator[VanwardDeviceState]):
    """Coordinator updated by WebSocket pushes."""

    def __init__(
        self, hass: HomeAssistant, client: VanwardApiClient, device_id: str
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=10),
        )
        self.client = client
        self.device_id = device_id

    async def _async_update_data(self) -> VanwardDeviceState:
        if self.client.auth_failed:
            raise ConfigEntryAuthFailed
        try:
            return await self.client.async_request_state(self.device_id)
        except VanwardSessionExpired:
            try:
                await self.client.async_relogin()
            except VanwardAuthError as err:
                raise ConfigEntryAuthFailed from err
            return await self.client.async_request_state(self.device_id)
        except VanwardAuthError as err:
            raise ConfigEntryAuthFailed from err

    async def async_start(self) -> None:
        if self.device_id in self.client.states:
            self.async_set_updated_data(self.client.states[self.device_id])

    async def async_shutdown(self) -> None:
        return

    @callback
    def async_state_updated(self, state: VanwardDeviceState) -> None:
        self.hass.loop.call_soon_threadsafe(self.async_set_updated_data, state)
