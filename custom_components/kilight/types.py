"""File for pure type definitions for KiLight."""

from homeassistant.config_entries import ConfigEntry

from kilight.client import Device

type KiLightConfigEntry = ConfigEntry[Device]
