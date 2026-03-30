"""Zerobyte integration for Home Assistant."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ZerobyteApiClient
from .const import CONF_EMAIL, CONF_HOST, CONF_PASSWORD, CONF_VERIFY_SSL
from .coordinator import ZerobyteDataUpdateCoordinator
from .data import ZerobyteData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import ZerobyteConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZerobyteConfigEntry,
) -> bool:
    """Set up Zerobyte from a config entry."""
    client = ZerobyteApiClient(
        host=entry.data[CONF_HOST],
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
        session=async_get_clientsession(
            hass, verify_ssl=entry.data.get(CONF_VERIFY_SSL, True)
        ),
        verify_ssl=entry.data.get(CONF_VERIFY_SSL, True),
    )

    await client.async_login()

    coordinator = ZerobyteDataUpdateCoordinator(hass)
    entry.runtime_data = ZerobyteData(client=client, coordinator=coordinator)

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ZerobyteConfigEntry,
) -> bool:
    """Unload a Zerobyte config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: ZerobyteConfigEntry,
) -> None:
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
