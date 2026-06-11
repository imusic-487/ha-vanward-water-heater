"""Config flow for the Vanward water heater integration."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

from .api import VanwardApiClient, VanwardAuthError
from .const import CONF_DEVICE_IDS, CONF_MOBILE, DOMAIN
from .protocol import VanwardDeviceState


class VanwardConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._mobile: str | None = None
        self._password: str | None = None
        self._states: dict[str, VanwardDeviceState] = {}
        self._existing_entry: ConfigEntry | None = None
        self._reauth_entry: ConfigEntry | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Start setup, reusing an existing account when possible."""

        existing = self._existing_account_entry()
        if existing is not None:
            self._existing_entry = existing
            self._mobile = existing.data[CONF_MOBILE]
            self._password = existing.data[CONF_PASSWORD]
            try:
                return await self._async_login_and_show_devices()
            except (VanwardAuthError, aiohttp.ClientError, TimeoutError, ValueError):
                self._mobile = None
                self._password = None
                return await self.async_step_account()

        return await self.async_step_account(user_input)

    async def async_step_account(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect account credentials."""

        errors: dict[str, str] = {}
        if user_input is not None:
            self._mobile = user_input[CONF_MOBILE]
            self._password = user_input[CONF_PASSWORD]
            try:
                return await self._async_login_and_show_devices()
            except VanwardAuthError:
                errors["base"] = "invalid_auth"
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            except ValueError:
                errors["base"] = "no_device"

        return self.async_show_form(
            step_id="account",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MOBILE): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Handle a reauth request from Home Assistant."""

        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect fresh credentials for an existing entry."""

        errors: dict[str, str] = {}
        if user_input is not None:
            self._mobile = user_input[CONF_MOBILE]
            self._password = user_input[CONF_PASSWORD]
            try:
                await self._async_login()
            except VanwardAuthError:
                errors["base"] = "invalid_auth"
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            except ValueError:
                errors["base"] = "no_device"
            else:
                assert self._reauth_entry is not None
                updated_data = {
                    **self._reauth_entry.data,
                    CONF_MOBILE: self._mobile,
                    CONF_PASSWORD: self._password,
                }
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry, data=updated_data
                )
                await self.hass.config_entries.async_reload(
                    self._reauth_entry.entry_id
                )
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MOBILE): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user select one or more unconfigured devices."""

        available = self._available_states()
        if not available:
            return self.async_abort(reason="no_unconfigured_devices")

        errors: dict[str, str] = {}
        if user_input is not None:
            selected = user_input[CONF_DEVICE_IDS]
            if not selected:
                errors["base"] = "no_device_selected"
            elif self._existing_entry is not None:
                existing_ids = [
                    str(device_id)
                    for device_id in self._existing_entry.data[CONF_DEVICE_IDS]
                ]
                updated_data = {
                    **self._existing_entry.data,
                    CONF_DEVICE_IDS: [*existing_ids, *selected],
                }
                self.hass.config_entries.async_update_entry(
                    self._existing_entry, data=updated_data
                )
                await self.hass.config_entries.async_reload(
                    self._existing_entry.entry_id
                )
                return self.async_abort(reason="devices_added")
            else:
                title = self._entry_title(selected)
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_MOBILE: self._mobile,
                        CONF_PASSWORD: self._password,
                        CONF_DEVICE_IDS: selected,
                    },
                )

        options = [
            {
                "value": device_id,
                "label": state.device_info.name or state.device_info.model or device_id,
            }
            for device_id, state in available.items()
        ]
        return self.async_show_form(
            step_id="devices",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_IDS): SelectSelector(
                        SelectSelectorConfig(options=options, multiple=True)
                    )
                }
            ),
            errors=errors,
        )

    async def _async_login_and_show_devices(self) -> ConfigFlowResult:
        assert self._mobile is not None
        assert self._password is not None

        await self._async_login()
        return await self.async_step_devices()

    async def _async_login(self) -> None:
        assert self._mobile is not None
        assert self._password is not None

        session = async_get_clientsession(self.hass)
        client = VanwardApiClient(
            session=session,
            mobile=self._mobile,
            password=self._password,
        )
        self._states = await client.async_fetch_devices()

    def _available_states(self) -> dict[str, VanwardDeviceState]:
        configured = self._configured_device_ids()
        return {
            device_id: state
            for device_id, state in self._states.items()
            if device_id not in configured
        }

    def _configured_device_ids(self) -> set[str]:
        device_ids: set[str] = set()
        for entry in self._async_current_entries():
            device_ids.update(
                str(device_id) for device_id in entry.data.get(CONF_DEVICE_IDS, [])
            )
        return device_ids

    def _existing_account_entry(self):
        entries = self._async_current_entries()
        return entries[0] if entries else None

    def _entry_title(self, selected: list[str]) -> str:
        names = [
            self._states[device_id].device_info.name
            or self._states[device_id].device_info.model
            or device_id
            for device_id in selected
        ]
        if len(names) == 1:
            return names[0]
        return f"万和热水器 ({len(names)})"
