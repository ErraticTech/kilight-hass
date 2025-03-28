"""Config flow for the KiLight integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS, CONF_HOST, CONF_PORT
from kilight.client import DEFAULT_PORT, Device
from kilight.client.exceptions import NetworkTimeoutError
import voluptuous as vol

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

_LOGGER = logging.getLogger(__name__)


class KiLightConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for KiLight."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: ZeroconfServiceInfo | None = None
        self._discovered_devices: dict[str, ZeroconfServiceInfo] = {}

    @property
    def discovered_devices(self) -> dict[str, ZeroconfServiceInfo]:
        """Return the list of discovered Zeroconf devices."""
        return self._discovered_devices

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the user step to pick discovered device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address_unique_id = user_input[CONF_ADDRESS]

            discovery_info = self.discovered_devices[address_unique_id]
            await self.async_set_unique_id(address_unique_id, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            device = Device(discovery_info.host, discovery_info.port)
            # noinspection PyBroadException
            try:
                await device.update_state()
                name = device.name
            except NetworkTimeoutError:
                _LOGGER.exception("Timed out during discovery state update")
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error")
                errors["base"] = "unknown"
            else:
                await device.disconnect()
                # Disable due to false-positive error for ConfigFlowResult type
                # noinspection PyTypeChecker
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_HOST: discovery_info.host,
                        CONF_PORT: discovery_info.port if discovery_info else DEFAULT_PORT,
                    },
                )

        if discovery := self._discovery_info:
            self._discovered_devices[discovery.properties["hwid"]] = discovery

        if not self.discovered_devices:
            # Disable due to false-positive error for ConfigFlowResult type
            # noinspection PyTypeChecker
            return self.async_abort(reason="no_devices_found")

        data_schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): vol.In(
                    {
                        service_info.properties["hwid"]: (
                            f"{service_info.hostname} ({service_info.host}:{service_info.port})"
                        )
                        for service_info in self.discovered_devices.values()
                    }
                )
            }
        )
        # Disable due to false-positive error for ConfigFlowResult type
        # noinspection PyTypeChecker
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> ConfigFlowResult:
        """Handle device found via zeroconf."""
        if discovery_info.ip_address.version == 6:  # noqa: PLR2004 IPv6 version is not an ambiguous magic number
            # Disable due to false-positive error for ConfigFlowResult type
            # noinspection PyTypeChecker
            return self.async_abort(reason="ipv6_not_supported")

        host = discovery_info.host
        port = discovery_info.port if discovery_info.port else DEFAULT_PORT
        hardware_id = discovery_info.properties["hwid"]

        _LOGGER.debug("Found KiLight device via zeroconf: %s:%s (%s)", host, port, hardware_id)

        device = Device(host, port)

        await device.update_state()

        self._discovery_info = discovery_info

        _LOGGER.debug(discovery_info)

        await self.async_set_unique_id(device.state.hardware_id)
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {"name": device.name}

        # Disable due to false-positive error for ConfigFlowResult type
        # noinspection PyTypeChecker
        return await self.async_step_user()
