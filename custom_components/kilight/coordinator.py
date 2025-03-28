"""The DataUpdateCoordinator subclass for the KiLight integration."""

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import UPDATE_EVERY_SECONDS
from .types import KiLightConfigEntry

if TYPE_CHECKING:
    from kilight.client import Device

_LOGGER = logging.getLogger(__name__)


class KiLightCoordinator(DataUpdateCoordinator[None]):
    """Class to manage fetching data."""

    def __init__(self, hass: HomeAssistant, entry: KiLightConfigEntry) -> None:
        """
        Initialize the Coordinator.

        :param HomeAssistant hass: Home Assistant instance, passed to super()
        :param KiLightConfigEntry entry: The config entry for KiLight
        """
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=entry.title,
            update_interval=timedelta(seconds=UPDATE_EVERY_SECONDS),
            always_update=True,
        )
        self._device: Device = entry.runtime_data

    async def _async_update_data(self) -> None:
        """Fetch the latest device state from the KiLight device."""
        try:
            _LOGGER.debug("Starting periodic refresh of KiLight data")
            await self._device.update_state()
        except Exception as err:
            raise UpdateFailed(str(err)) from err
