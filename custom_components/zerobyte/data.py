"""Custom types for the Zerobyte integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .api import ZerobyteApiClient
    from .coordinator import ZerobyteDataUpdateCoordinator


type ZerobyteConfigEntry = ConfigEntry[ZerobyteData]


@dataclass
class ZerobyteData:
    """Runtime data for the Zerobyte integration."""

    client: ZerobyteApiClient
    coordinator: ZerobyteDataUpdateCoordinator
