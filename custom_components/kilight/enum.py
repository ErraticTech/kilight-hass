"""Enums specific to the HomeAssistant KiLight integration."""

from enum import Enum


class TemperatureSensorLocation(Enum):
    """Location of a temperature sensor."""

    Driver = 1
    PowerSupply = 2
    OutputA = 3
    OutputB = 4
