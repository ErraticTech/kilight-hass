"""The KiLight integration models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kilight.client import Device

    from .coordinator import KiLightCoordinator


@dataclass
class KiLightDeviceData:
    """Data for the KiLight integration."""

    title: str
    device: Device
    coordinator: KiLightCoordinator
