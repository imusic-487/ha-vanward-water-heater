"""Vanward water heater integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import VanwardApiClient, VanwardAuthError
from .const import CONF_DEVICE_IDS, CONF_MOBILE, DOMAIN, PLATFORMS
from .coordinator import VanwardCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""

    session = async_get_clientsession(hass)
    client = VanwardApiClient(
        session=session,
        mobile=entry.data[CONF_MOBILE],
        password=entry.data[CONF_PASSWORD],
    )
    try:
        states = await client.async_fetch_devices()
    except VanwardAuthError as err:
        raise ConfigEntryAuthFailed from err
    except Exception as err:
        raise ConfigEntryNotReady from err

    coordinators: dict[str, VanwardCoordinator] = {}
    for device_id in entry.data[CONF_DEVICE_IDS]:
        device_id = str(device_id)
        state = states.get(device_id)
        if state is None:
            _LOGGER.warning(
                "Configured Vanward device %s was not returned by the account",
                device_id,
            )
            continue
        coordinator = VanwardCoordinator(hass, client, device_id)
        coordinators[device_id] = coordinator
        coordinator.async_set_updated_data(state)

    if not coordinators:
        raise ConfigEntryNotReady("No configured Vanward devices are currently available")

    @callback
    def _state_updated(device_id: str, state) -> None:
        if coordinator := coordinators.get(device_id):
            coordinator.async_state_updated(state)

    @callback
    def _auth_failed() -> None:
        hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))

    client.set_state_callback(_state_updated)
    client.set_auth_failed_callback(_auth_failed)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinators": coordinators,
    }
    try:
        await client.async_connect()
    except VanwardAuthError as err:
        await client.async_disconnect()
        hass.data[DOMAIN].pop(entry.entry_id, None)
        raise ConfigEntryAuthFailed from err
    except Exception as err:
        await client.async_disconnect()
        hass.data[DOMAIN].pop(entry.entry_id, None)
        raise ConfigEntryNotReady from err

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    data = hass.data[DOMAIN].pop(entry.entry_id)
    await data["client"].async_disconnect()
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
