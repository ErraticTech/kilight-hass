"""Test the KiLight config flow."""

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.const import CONF_ADDRESS, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from kilight.client.exceptions import NetworkTimeoutError

from custom_components.kilight.const import DOMAIN


async def test_form(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_unload_entry: AsyncMock,
    mock_device_update_state: AsyncMock,
    mock_zeroconf_devices: dict[str, ZeroconfServiceInfo],
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch("kilight.client.Device.name", new="Mock Device"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ADDRESS: "mock",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Mock Device"
    assert result["data"] == {CONF_HOST: "1.1.1.1", CONF_PORT: 1234}
    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_device_update_state.mock_calls) == 1

    await hass.config_entries.async_remove(result["result"].entry_id)
    assert len(mock_unload_entry.mock_calls) == 1


async def test_form_cannot_connect(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_unload_entry: AsyncMock,
    mock_device_update_state: AsyncMock,
    mock_zeroconf_devices: dict[str, ZeroconfServiceInfo],
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "kilight.client.Device.update_state",
        return_value=None,
        side_effect=NetworkTimeoutError("Test"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_ADDRESS: "mock"}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    # Make sure the config flow tests finish with either an
    # FlowResultType.CREATE_ENTRY or FlowResultType.ABORT so
    # we can show the config flow is able to recover from an error.

    await test_form(
        hass,
        mock_setup_entry,
        mock_unload_entry,
        mock_device_update_state,
        mock_zeroconf_devices,
    )
