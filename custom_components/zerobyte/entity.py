"""Base entity for the Zerobyte integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_HOST, DOMAIN
from .coordinator import ZerobyteDataUpdateCoordinator


class ZerobyteEntity(CoordinatorEntity[ZerobyteDataUpdateCoordinator]):
    """Base class for Zerobyte entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ZerobyteDataUpdateCoordinator,
        entity_key: str,
    ) -> None:
        super().__init__(coordinator)
        host = coordinator.config_entry.data[CONF_HOST].rstrip("/")
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{entity_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=f"Zerobyte ({host})",
            manufacturer="Zerobyte",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=host,
        )
