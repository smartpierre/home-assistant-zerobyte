"""DataUpdateCoordinator for the Zerobyte integration."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import (
    ZerobyteApiClientAuthenticationError,
    ZerobyteApiClientError,
)
from .const import DEFAULT_SCAN_INTERVAL, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import ZerobyteConfigEntry


class ZerobyteDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls backups, volumes, and repositories."""

    config_entry: ZerobyteConfigEntry

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(
            hass,
            LOGGER,
            name="zerobyte",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch all data from the Zerobyte API."""
        client = self.config_entry.runtime_data.client
        try:
            volumes = await client.async_get_volumes()
            repositories = await client.async_get_repositories()
            backups = await client.async_get_backups()

            for repo in repositories:
                try:
                    stats = await client.async_get_repository_stats(
                        repo["shortId"]
                    )
                    repo["stats"] = stats
                except ZerobyteApiClientError:
                    repo["stats"] = {}

            return {
                "volumes": volumes,
                "repositories": repositories,
                "backups": backups,
            }
        except ZerobyteApiClientAuthenticationError as exc:
            raise ConfigEntryAuthFailed(exc) from exc
        except ZerobyteApiClientError as exc:
            raise UpdateFailed(f"Error fetching Zerobyte data: {exc}") from exc
