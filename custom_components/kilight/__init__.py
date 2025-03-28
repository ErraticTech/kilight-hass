"""The KiLight integration."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from homeassistant.const import CONF_HOST, CONF_PORT, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.exceptions import ConfigEntryNotReady
from kilight.client import DEFAULT_PORT, Device

from .const import DEVICE_TIMEOUT_SECONDS, DOMAIN
from .coordinator import KiLightCoordinator
from .models import KiLightDeviceData

if TYPE_CHECKING:
    from homeassistant.core import Event, HomeAssistant

    from .types import KiLightConfigEntry

_PLATFORMS: list[Platform] = [Platform.LIGHT, Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: KiLightConfigEntry) -> bool:
    """Set up KiLight from a config entry."""
    host: str = entry.data[CONF_HOST]
    port: int = entry.data.get(CONF_PORT, DEFAULT_PORT)

    device = Device(host, port)

    entry.runtime_data = device

    startup_event = asyncio.Event()
    cancel_first_update = device.register_callback(lambda *_: startup_event.set())
    kilight_coordinator = KiLightCoordinator(hass, entry=entry)

    try:
        await kilight_coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady:
        cancel_first_update()
        raise

    try:
        async with asyncio.timeout(DEVICE_TIMEOUT_SECONDS):
            await startup_event.wait()
    except TimeoutError as ex:
        error_msg = (
            f'Unable to communicate with "{device.name}"; Please make sure the'
            f" device is connected to the network."
        )
        raise ConfigEntryNotReady(error_msg) from ex
    finally:
        cancel_first_update()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = KiLightDeviceData(
        entry.title, device, kilight_coordinator
    )

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    async def _async_stop(_: Event) -> None:
        """Close the connection cleanly."""
        await device.disconnect()

    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_stop))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: KiLightConfigEntry) -> bool:
    """
    Clean up on Home Assistant unload.

    Ensure the KiLight is disconnected and removed when HomeAssistant tells us to unload
    it.
    """
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, _PLATFORMS):
        data: KiLightDeviceData = hass.data[DOMAIN].pop(entry.entry_id)
        await data.device.disconnect()

    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: KiLightConfigEntry) -> None:
    data: KiLightDeviceData = hass.data[DOMAIN][entry.entry_id]
    if entry.title != data.title:
        await hass.config_entries.async_reload(entry.entry_id)
