"""Common fixtures for the KiLight tests."""

from collections.abc import Generator
from ipaddress import IPv4Address
from typing import Any
from unittest.mock import AsyncMock, patch

from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
import pytest


# noinspection PyUnusedLocal
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: Any) -> None:
    """
    Require the enable_custom_integrations fixture.

    Necessary for home assistant testing to work with custom integrations.
    """


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "custom_components.kilight.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_unload_entry() -> Generator[AsyncMock]:
    """Override mock_unload_entry."""
    with patch(
        "custom_components.kilight.async_unload_entry", return_value=True
    ) as mock_unload_entry:
        yield mock_unload_entry


@pytest.fixture
def mock_device_update_state() -> Generator[AsyncMock]:
    """Override update_state, the bit that actually does the network interactions."""
    with patch("kilight.client.Device.update_state", return_value=None) as mock_device_update_state:
        yield mock_device_update_state


@pytest.fixture
def mock_zeroconf_devices() -> Generator[dict[str, ZeroconfServiceInfo]]:
    """Mock the list of found zeroconf devices."""
    mock_devices: dict[str, ZeroconfServiceInfo] = {
        "mock": ZeroconfServiceInfo(
            hostname="mock.hostname",
            ip_address=IPv4Address("1.1.1.1"),
            port=1234,
            ip_addresses=[IPv4Address("1.1.1.1")],
            type="mock",
            name="mock",
            properties={"hwid": "mock"},
        )
    }
    with patch(
        "custom_components.kilight.config_flow.KiLightConfigFlow.discovered_devices",
        new=mock_devices,
    ) as mock_discovered_devices:
        yield mock_discovered_devices
