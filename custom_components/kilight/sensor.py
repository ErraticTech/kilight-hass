"""KiLight integration, sensors platform."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    UnitOfElectricCurrent,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from kilight.client import Device, OutputIdentifier, OutputIdUtil

from .const import DOMAIN
from .entity import KiLightBaseEntity, KiLightOutputBaseEntity
from .enum import TemperatureSensorLocation
from .exceptions import UnknownTemperatureSensorError

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import KiLightCoordinator
    from .models import KiLightDeviceData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    data: KiLightDeviceData = hass.data[DOMAIN][entry.entry_id]
    # All KiLight devices have OutputA and the system-level sensors
    entities_to_add = [
        KiLightOutputCurrentEntity(
            data.coordinator, data.device, OutputIdentifier.OutputA, entry.title
        ),
        KiLightTemperatureEntity(
            data.coordinator,
            data.device,
            TemperatureSensorLocation.OutputA,
            entry.title,
        ),
        KiLightTemperatureEntity(
            data.coordinator, data.device, TemperatureSensorLocation.Driver, entry.title
        ),
        KiLightTemperatureEntity(
            data.coordinator,
            data.device,
            TemperatureSensorLocation.PowerSupply,
            entry.title,
        ),
        KiLightFanSpeedEntity(data.coordinator, data.device, entry.title),
        KiLightFanDrivePercentageEntity(data.coordinator, data.device, entry.title),
    ]

    if data.device.state.output_b is not None:
        entities_to_add.append(
            KiLightOutputCurrentEntity(
                data.coordinator, data.device, OutputIdentifier.OutputB, entry.title
            )
        )
        entities_to_add.append(
            KiLightTemperatureEntity(
                data.coordinator,
                data.device,
                TemperatureSensorLocation.OutputB,
                entry.title,
            )
        )

    async_add_entities(entities_to_add)


class KiLightOutputCurrentEntity(KiLightOutputBaseEntity, SensorEntity):
    """Representation of KiLight light driver output current sensor."""

    _attr_name: str | None = None
    _attr_translation_key = "output_current"

    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_suggested_display_precision = 3
    _attr_icon = "mdi:current-dc"

    def __init__(
        self,
        coordinator: KiLightCoordinator,
        device: Device,
        output: OutputIdentifier,
        name: str,
    ) -> None:
        """
        Initialize the output current entity.

        :param KiLightCoordinator coordinator: KiLight coordinator
        :param Device device: KiLight device
        :param OutputIdentifier output: Which output this measures the current of
        :param str name: Name to pass through to the DeviceInfo instance
        """
        super().__init__(coordinator, device, output, name)
        self._attr_unique_id = f"{self._attr_unique_id}_current"
        self._attr_name = f"Output {OutputIdUtil.letter(output)} Current"
        self._attr_translation_placeholders = {"output_id": OutputIdUtil.letter(output)}
        self._async_update_attrs()

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        if self.output_state is not None:
            self._attr_native_value = self.output_state.current


class KiLightTemperatureEntity(KiLightBaseEntity, SensorEntity):
    """Representation of a temperature sensor on a KiLight."""

    _attr_name: str | None = None
    _attr_translation_key = "component_temperature"

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: KiLightCoordinator,
        device: Device,
        temperature_sensor: TemperatureSensorLocation,
        name: str,
    ) -> None:
        """
        Initialize the temperature sensor entity.

        :param KiLightCoordinator coordinator: KiLight coordinator
        :param Device device: KiLight device
        :param TemperatureSensorLocation temperature_sensor: Location of the sensor
        :param str name: Name to pass through to the DeviceInfo instance
        """
        super().__init__(coordinator, device, name)
        self._temperature_sensor = temperature_sensor
        self._attr_unique_id = f"{self._attr_unique_id}_{temperature_sensor.name}_temperature"
        self._attr_name = f"{self.temperature_sensor_display_name} Temperature"
        self._attr_translation_placeholders = {
            "sensor_location_name": self.temperature_sensor_display_name
        }
        self._async_update_attrs()

    @property
    def temperature_sensor_display_name(self) -> str:
        """User-friendly display name of this temperature sensor."""
        if self._temperature_sensor == TemperatureSensorLocation.Driver:
            return "Driver"

        if self._temperature_sensor == TemperatureSensorLocation.PowerSupply:
            return "Power Supply"

        if self._temperature_sensor == TemperatureSensorLocation.OutputA:
            return "Output A"

        if self._temperature_sensor == TemperatureSensorLocation.OutputB:
            return "Output B"

        return self._temperature_sensor.name

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        if self._temperature_sensor == TemperatureSensorLocation.Driver:
            if self.device.state.driver_temperature is not None:
                self._attr_native_value = self.device.state.driver_temperature.celsius
        elif self._temperature_sensor == TemperatureSensorLocation.PowerSupply:
            if self.device.state.power_supply_temperature is not None:
                self._attr_native_value = self.device.state.power_supply_temperature.celsius
        elif self._temperature_sensor == TemperatureSensorLocation.OutputA:
            if self.device.state.output_a.temperature is not None:
                self._attr_native_value = self.device.state.output_a.temperature.celsius
        elif self._temperature_sensor == TemperatureSensorLocation.OutputB:
            if (
                self.device.state.output_b is not None
                and self.device.state.output_b.temperature is not None
            ):
                self._attr_native_value = self.device.state.output_b.temperature.celsius
        else:
            raise UnknownTemperatureSensorError(self._temperature_sensor)


class KiLightFanSpeedEntity(KiLightBaseEntity, SensorEntity):
    """Representation of KiLight internal fan speed in RPM."""

    _attr_name: str | None = None
    _attr_translation_key = "fan_speed"

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = REVOLUTIONS_PER_MINUTE
    _attr_suggested_display_precision = 0
    _attr_icon = "mdi:fan"

    def __init__(self, coordinator: KiLightCoordinator, device: Device, name: str) -> None:
        """
        Initialize the Fan Speed entity.

        :param KiLightCoordinator coordinator: KiLight coordinator
        :param Device device: KiLight device
        :param str name: Name to pass through to the DeviceInfo instance
        """
        super().__init__(coordinator, device, name)
        self._attr_unique_id = f"{self._attr_unique_id}_fan_speed"
        self._attr_name = "Fan Speed"
        self._async_update_attrs()

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        self._attr_native_value = self.device.state.fan_speed


class KiLightFanDrivePercentageEntity(KiLightBaseEntity, SensorEntity):
    """Representation of KiLight internal fan drive percentage."""

    _attr_name: str | None = None
    _attr_translation_key = "fan_drive_percentage"

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 1
    _attr_icon = "mdi:fan"

    def __init__(self, coordinator: KiLightCoordinator, device: Device, name: str) -> None:
        """
        Initialize the Fan Drive Percentage Entity.

        :param KiLightCoordinator coordinator: KiLight coordinator
        :param Device device: KiLight device
        :param str name: Name to pass through to the DeviceInfo instance
        """
        super().__init__(coordinator, device, name)
        self._attr_unique_id = f"{self._attr_unique_id}_fan_drive_percentage"
        self._attr_name = "Fan Drive Level"
        self._async_update_attrs()

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        self._attr_native_value = self.device.state.fan_drive_percentage
