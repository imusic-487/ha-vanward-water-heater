"""Cloud client for Vanward water heaters."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import suppress
import logging
from typing import Any

import aiohttp

from .const import (
    COMMAND_HEARTBEAT,
    COMMAND_LOGIN,
    COMMAND_STATUS_REPORT,
    LOGIN_URL,
    WS_URL,
)
from .protocol import (
    VanwardDeviceState,
    decode_message,
    encode_message,
    press_call,
    set_bathroom_mode,
    set_boost,
    set_cruise_mode,
    set_cruise_temperature,
    set_enjoy_cruise,
    set_power,
    set_single_cruise,
    set_target_temperature,
    states_from_login_payload,
    state_from_status,
    update_status_payload,
)

_LOGGER = logging.getLogger(__name__)

StateCallback = Callable[[str, VanwardDeviceState], None]
AuthFailedCallback = Callable[[], None]


class VanwardApiError(Exception):
    """Base API error."""


class VanwardAuthError(VanwardApiError):
    """Authentication failed."""


class VanwardSessionExpired(VanwardAuthError):
    """Cloud session is no longer valid."""


class VanwardApiClient:
    """Async client for the Vanward cloud API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        mobile: str,
        password: str,
    ) -> None:
        self._session = session
        self._mobile = mobile
        self._password = password
        self._user_id: str | None = None
        self._token: str | None = None
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._listen_task: asyncio.Task[None] | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._state_callback: StateCallback | None = None
        self._auth_failed_callback: AuthFailedCallback | None = None
        self.auth_failed = False
        self.states: dict[str, VanwardDeviceState] = {}

    @property
    def connected(self) -> bool:
        return self._ws is not None and not self._ws.closed

    def set_state_callback(self, callback: StateCallback) -> None:
        self._state_callback = callback

    def set_auth_failed_callback(self, callback: AuthFailedCallback) -> None:
        self._auth_failed_callback = callback

    async def async_login(self) -> dict[str, VanwardDeviceState]:
        """Login via HTTP and cache token plus initial device states."""

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json, text/plain, */*",
        }
        async with self._session.post(
            LOGIN_URL,
            data={"mobile": self._mobile, "password": self._password},
            headers=headers,
        ) as response:
            if response.status >= 400:
                raise VanwardAuthError(f"Login failed with HTTP {response.status}")
            payload = await response.json(content_type=None)

        user = payload.get("User") or payload.get("user")
        if not user or not user.get("Token") or not user.get("Uuid"):
            raise VanwardAuthError("Login response did not contain User.Token/Uuid")

        self._token = user["Token"]
        self._user_id = user["Uuid"]
        self.auth_failed = False
        self.states = states_from_login_payload(payload)
        for device_id, state in self.states.items():
            self._notify_state(device_id, state)
        return self.states

    async def async_relogin(self) -> dict[str, VanwardDeviceState]:
        """Refresh HTTP token and reconnect WebSocket."""

        await self.async_disconnect()
        states = await self.async_login()
        await self.async_connect()
        return states

    async def async_refresh_session(self) -> None:
        """Refresh token and re-login on the current WebSocket."""

        await self.async_login()
        if self.connected and self._ws is not None:
            await self._ws.send_bytes(
                encode_message(
                    COMMAND_LOGIN, {"Id": self._user_id, "Token": self._token}
                )
            )

    async def async_connect(self) -> None:
        """Open WebSocket connection and start background listeners."""

        if self._token is None or self._user_id is None:
            await self.async_login()
        await self.async_disconnect()
        self._ws = await self._session.ws_connect(WS_URL)
        await self._ws.send_bytes(
            encode_message(COMMAND_LOGIN, {"Id": self._user_id, "Token": self._token})
        )
        self._listen_task = asyncio.create_task(self._listen_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def async_disconnect(self) -> None:
        """Close the WebSocket and background tasks."""

        for task in (self._listen_task, self._heartbeat_task):
            if task is not None:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
        self._listen_task = None
        self._heartbeat_task = None
        if self._ws is not None and not self._ws.closed:
            await self._ws.close()
        self._ws = None

    async def async_request_state(self, device_id: str) -> VanwardDeviceState:
        """Reconnect and let the cloud push the current state."""

        if not self.connected:
            await self.async_connect()
        return self.states[device_id]

    async def async_set_power(self, device_id: str, enabled: bool) -> None:
        await self._mutate_and_send(device_id, lambda state: set_power(state, enabled))

    async def async_set_boost(self, device_id: str, enabled: bool) -> None:
        await self._mutate_and_send(device_id, lambda state: set_boost(state, enabled))

    async def async_set_single_cruise(self, device_id: str, enabled: bool) -> None:
        await self._mutate_and_send(
            device_id, lambda state: set_single_cruise(state, enabled)
        )

    async def async_set_enjoy_cruise(self, device_id: str, enabled: bool) -> None:
        await self._mutate_and_send(
            device_id, lambda state: set_enjoy_cruise(state, enabled)
        )

    async def async_set_target_temperature(
        self, device_id: str, temperature: int
    ) -> None:
        await self._mutate_and_send(
            device_id,
            lambda state: set_target_temperature(state, temperature)
        )

    async def async_set_cruise_temperature(
        self, device_id: str, temperature: int
    ) -> None:
        await self._mutate_and_send(
            device_id,
            lambda state: set_cruise_temperature(state, temperature)
        )

    async def async_set_cruise_mode(self, device_id: str, option: str) -> None:
        await self._mutate_and_send(
            device_id, lambda state: set_cruise_mode(state, option)
        )

    async def async_set_bathroom_mode(self, device_id: str, option: str) -> None:
        await self._mutate_and_send(
            device_id, lambda state: set_bathroom_mode(state, option)
        )

    async def async_press_call(self, device_id: str) -> None:
        await self._mutate_and_send(device_id, press_call)

    async def _mutate_and_send(
        self, device_id: str, mutator: Callable[[VanwardDeviceState], bool]
    ) -> None:
        if not self.states:
            await self.async_login()
        state = self.states[device_id]

        changed = mutator(state)
        if not changed:
            return
        command, payload = update_status_payload(state)
        try:
            await self._send_raw(command, payload)
        except VanwardSessionExpired:
            await self.async_relogin()
            await self._send_raw(command, payload)
        self._notify_state(device_id, state)

    async def _send_raw(self, command: int, payload: dict[str, Any] | None = None) -> None:
        if not self.connected:
            await self.async_connect()
        if self._ws is None:
            raise VanwardApiError("WebSocket is not connected")
        await self._ws.send_bytes(encode_message(command, payload))

    async def _listen_loop(self) -> None:
        while self._ws is not None:
            try:
                message = await self._ws.receive()
                if message.type == aiohttp.WSMsgType.BINARY:
                    await self._handle_binary(message.data)
                elif message.type in (
                    aiohttp.WSMsgType.CLOSE,
                    aiohttp.WSMsgType.CLOSED,
                    aiohttp.WSMsgType.ERROR,
                ):
                    break
            except asyncio.CancelledError:
                raise
            except VanwardSessionExpired:
                _LOGGER.warning("Vanward session expired, refreshing login")
                try:
                    await self.async_refresh_session()
                except VanwardAuthError:
                    self.auth_failed = True
                    _LOGGER.exception("Vanward reauthentication failed")
                    if self._auth_failed_callback is not None:
                        self._auth_failed_callback()
                    break
            except Exception:
                _LOGGER.exception("Error while reading Vanward WebSocket message")
                await asyncio.sleep(5)

    async def _heartbeat_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(40)
                if self.connected:
                    await self._send_raw(COMMAND_HEARTBEAT)
            except asyncio.CancelledError:
                raise
            except Exception:
                _LOGGER.exception("Error while sending Vanward heartbeat")

    async def _handle_binary(self, data: bytes) -> None:
        command, payload = decode_message(data)
        if _payload_indicates_auth_error(payload):
            raise VanwardSessionExpired("Vanward session expired")
        if command == COMMAND_LOGIN:
            self.states = states_from_login_payload(payload)
            for device_id, state in self.states.items():
                self._notify_state(device_id, state)
        elif command == COMMAND_STATUS_REPORT and self.states:
            status = payload.get("data", {}).get("Status") or payload.get("Status")
            device_id = (
                payload.get("data", {}).get("DeviceId")
                or payload.get("data", {}).get("Id")
                or payload.get("DeviceId")
                or payload.get("Id")
            )
            if device_id is None and len(self.states) == 1:
                device_id = next(iter(self.states))
            if status is not None:
                state = self.states.get(device_id)
                if state is None:
                    _LOGGER.debug(
                        "Ignoring status report for unknown device id: %s", device_id
                    )
                    return
                self.states[device_id] = state_from_status(status, state.device_info)
                self._notify_state(device_id, self.states[device_id])

    def _notify_state(self, device_id: str, state: VanwardDeviceState) -> None:
        if self._state_callback is not None:
            self._state_callback(device_id, state)


def _payload_indicates_auth_error(payload: dict[str, Any]) -> bool:
    code = payload.get("code") or payload.get("Code") or payload.get("errorCode")
    message = str(
        payload.get("message") or payload.get("Message") or payload.get("msg") or ""
    ).lower()
    if code in (401, 403, "401", "403", -401, "-401"):
        return True
    return any(text in message for text in ("token", "auth", "login", "unauthorized"))
