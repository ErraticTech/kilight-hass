"""Base entity classes for KiLight entities."""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
import logging
from typing import Any

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from kilight.client import Device, OutputIdentifier, OutputState

from .const import DOMAIN
from .coordinator import KiLightCoordinator
from .exceptions import UnknownOutputError

_LOGGER = logging.getLogger(__name__)


class KiLightBaseEntity(CoordinatorEntity[KiLightCoordinator], Entity, metaclass=ABCMeta):
    """Base class for deriving KiLight entities from."""

    _attr_has_entity_name: bool = True

    def __init__(self, coordinator: KiLightCoordinator, device: Device, name: str) -> None:
        """
        Initialize the KiLight entity.

        :param KiLightCoordinator coordinator: KiLight coordinator
        :param Device device: KiLight device
        :param str name: Name to pass through to the DeviceInfo instance
        """
        super().__init__(coordinator)
        self._device: Device = device
        self._attr_device_info: DeviceInfo = DeviceInfo(
            identifiers={(DOMAIN, device.state.hardware_id)},
            name=name,
            manufacturer=device.state.manufacturer_name,
            model=device.state.model,
            sw_version=str(device.state.firmware_version),
            hw_version=str(device.state.hardware_version),
        )
        self._attr_unique_id = device.state.hardware_id

    @property
    def device(self) -> Device:
        """The Device instance, used to control the physical KiLight hardware."""
        return self._device

    @callback
    @abstractmethod
    def _async_update_attrs(self) -> None:
        """
        Handle updating _attr values.

        Override this in derived classes.
        """

    @callback
    def _handle_coordinator_update(self, *_: Any) -> None:
        """Handle data update."""
        self._async_update_attrs()
        self.async_write_ha_state()

    def _register_update_callback(self) -> None:
        """
        Bind to the device-wide update callback.

        Override this in subclasses to bind to more specific update callbacks.
        """
        self.async_on_remove(self.device.register_callback(self._handle_coordinator_update))

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        await super().async_added_to_hass()
        self._register_update_callback()


class KiLightOutputBaseEntity(KiLightBaseEntity, metaclass=ABCMeta):
    """Base class for deriving KiLight output-specific entities from."""

    def __init__(
        self,
        coordinator: KiLightCoordinator,
        device: Device,
        output: OutputIdentifier,
        name: str,
    ) -> None:
        """
        Initialize the output entity.

        :param KiLightCoordinator coordinator: KiLight coordinator
        :param Device device: KiLight device
        :param OutputIdentifier output: Which output this entity is related to
        :param str name: Name to pass through to the DeviceInfo instance
        """
        super().__init__(coordinator, device, name)
        self._output: OutputIdentifier = output
        self._attr_unique_id = f"{self._attr_unique_id}_{OutputIdentifier.Name(self._output)}"

    @property
    def output(self) -> OutputIdentifier:
        """Which output this entity represents."""
        return self._output

    @property
    def output_state(self) -> OutputState | None:
        """Get the state of this output from the device state."""
        if self.output == OutputIdentifier.OutputA:
            return self.device.state.output_a
        if self.output == OutputIdentifier.OutputB:
            return self.device.state.output_b
        raise UnknownOutputError(self.output)
