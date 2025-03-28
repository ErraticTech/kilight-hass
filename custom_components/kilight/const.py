"""Constants for the KiLight integration."""

from typing import Final

# HASS Domain of the integration
DOMAIN: Final[str] = "kilight"

# How frequently to query the device for a state update, in seconds
UPDATE_EVERY_SECONDS: Final[int] = 30

# Overall timeout during operations to make sure we don't hang.
# KiLight has its own timeout handling, but in case that fails this should catch it.
DEVICE_TIMEOUT_SECONDS: Final[int] = 30
