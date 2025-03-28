"""Exceptions specific to the KiLight integration."""

from custom_components.kilight.enum import TemperatureSensorLocation
from kilight.protocol import OutputIdentifier


class UnknownOutputError(ValueError):
    """Specific ValueError for an unknown OutputIdentifier."""

    def __init__(self, unknown_id: OutputIdentifier) -> None:
        """Initialize with the given unknown output ID."""
        super().__init__(f"Unknown output: {OutputIdentifier.Name(unknown_id)}")


class UnknownTemperatureSensorError(ValueError):
    """Specific ValueError for an unknown TemperatureSensorLocation."""

    def __init__(self, unknown_temp_sensor: TemperatureSensorLocation) -> None:
        """Initialize with the given unknown temperature sensor location."""
        super().__init__(f"Unknown temperature sensor: {unknown_temp_sensor.name}")
