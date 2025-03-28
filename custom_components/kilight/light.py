"""KiLight integration, light platform."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Final

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_RGBWW_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.core import HomeAssistant, callback
from kilight.client import (
    MAX_COLOR_TEMP,
    MIN_COLOR_TEMP,
    Device,
    OutputIdentifier,
    OutputIdUtil,
)

from .const import DOMAIN
from .entity import KiLightOutputBaseEntity

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
    """Set up the light platform."""
    data: KiLightDeviceData = hass.data[DOMAIN][entry.entry_id]
    # All KiLights have at least Output A
    entities_to_add = [
        KiLightOutputLightEntity(
            data.coordinator, data.device, OutputIdentifier.OutputA, entry.title
        )
    ]

    if data.device.state.output_b is not None:
        entities_to_add.append(
            KiLightOutputLightEntity(
                data.coordinator, data.device, OutputIdentifier.OutputB, entry.title
            )
        )
    async_add_entities(entities_to_add)


class KiLightOutputLightEntity(KiLightOutputBaseEntity, LightEntity):
    """Representation of a single light output of a KiLight."""

    _attr_translation_key: Final[str] = "output_light"

    _attr_supported_color_modes: Final[set[ColorMode]] = {
        ColorMode.COLOR_TEMP,
        ColorMode.RGBWW,
    }
    _attr_supported_features: Final[LightEntityFeature] = LightEntityFeature(0)
    _attr_min_color_temp_kelvin: Final[int] = MIN_COLOR_TEMP
    _attr_max_color_temp_kelvin: Final[int] = MAX_COLOR_TEMP

    def __init__(
        self,
        coordinator: KiLightCoordinator,
        device: Device,
        output: OutputIdentifier,
        name: str,
    ) -> None:
        """
        Initialize the output light entity.

        :param KiLightCoordinator coordinator: KiLight coordinator
        :param Device device: KiLight device
        :param OutputIdentifier output: Which output this entity represents
        :param str name: Name to pass through to the DeviceInfo instance
        """
        super().__init__(coordinator, device, output, name)
        self._attr_unique_id = f"{self._attr_unique_id}_light"
        self._attr_name = f"Output {OutputIdUtil.letter(output)} Light"
        self._attr_color_mode = ColorMode.RGBWW
        self._attr_translation_placeholders = {"output_id": OutputIdUtil.letter(output)}
        self._async_update_attrs()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on and set its brightness/color."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        rgbww_color = kwargs.get(ATTR_RGBWW_COLOR)
        color_temp = kwargs.get(ATTR_COLOR_TEMP_KELVIN)

        _LOGGER.debug("%s turning on, kwargs = %s", self.name, f"{kwargs}")

        updates = {}

        if brightness is not None:
            updates["brightness"] = brightness

        if rgbww_color is not None:
            self._attr_color_mode = ColorMode.RGBWW
            updates["rgbcw_color"] = rgbww_color
        elif color_temp is not None:
            self._attr_color_mode = ColorMode.COLOR_TEMP
            updates["color_temp"] = color_temp

        updates["power_on"] = True

        await self.device.update_output_from_parts(self.output, **updates)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        _LOGGER.debug("%s turning off, kwargs = %s", self.name, f"{kwargs}")
        await self.device.write_output(self.output, power_on=False)

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        if self.output == OutputIdentifier.OutputA:
            output_state = self.device.state.output_a
        elif self.output == OutputIdentifier.OutputB:
            output_state = self.device.state.output_b
        else:
            return

        if output_state is None:
            return

        self._attr_brightness = output_state.brightness
        self._attr_rgbww_color = output_state.rgbcw
        self._attr_color_temp_kelvin = output_state.color_temp
        self._attr_is_on = output_state.power_on
        _LOGGER.debug(
            "%s Output %s updated values - "
            "brightness: %s, rgbww_color: %s, color_temp: %s, is_on: %s",
            self.name,
            OutputIdentifier.Name(self.output),
            self._attr_brightness,
            self._attr_rgbww_color,
            self._attr_color_temp_kelvin,
            self._attr_is_on,
        )
