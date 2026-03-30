"""Sensor platform for the Zerobyte integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import ZerobyteDataUpdateCoordinator
from .data import ZerobyteConfigEntry
from .entity import ZerobyteEntity


def _epoch_to_datetime(value: int | float | None) -> datetime | None:
    """Convert a Unix epoch (seconds) to a timezone-aware datetime."""
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


# ---------------------------------------------------------------------------
# Descriptor dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class ZerobyteSensorEntityDescription(SensorEntityDescription):
    """Describe a Zerobyte sensor."""

    collection: str  # "backups", "volumes", or "repositories"
    resource_prefix: str  # "Backup", "Volume", or "Repository"
    value_fn: Callable[[dict[str, Any]], Any]
    item_name_key: str = "name"


# ---------------------------------------------------------------------------
# Backup schedule sensors
# ---------------------------------------------------------------------------

BACKUP_SENSORS: tuple[ZerobyteSensorEntityDescription, ...] = (
    ZerobyteSensorEntityDescription(
        key="backup_status",
        translation_key="backup_status",
        name="Status",
        icon="mdi:backup-restore",
        collection="backups",
        resource_prefix="Backup",
        value_fn=lambda b: b.get("lastBackupStatus", "unknown"),
    ),
    ZerobyteSensorEntityDescription(
        key="backup_last",
        translation_key="backup_last",
        name="Last backup",
        device_class=SensorDeviceClass.TIMESTAMP,
        collection="backups",
        resource_prefix="Backup",
        value_fn=lambda b: _epoch_to_datetime(b.get("lastBackupAt")),
    ),
    ZerobyteSensorEntityDescription(
        key="backup_next",
        translation_key="backup_next",
        name="Next backup",
        device_class=SensorDeviceClass.TIMESTAMP,
        collection="backups",
        resource_prefix="Backup",
        value_fn=lambda b: _epoch_to_datetime(b.get("nextBackupAt")),
    ),
)

# ---------------------------------------------------------------------------
# Volume sensors
# ---------------------------------------------------------------------------

VOLUME_SENSORS: tuple[ZerobyteSensorEntityDescription, ...] = (
    ZerobyteSensorEntityDescription(
        key="volume_status",
        translation_key="volume_status",
        name="Status",
        icon="mdi:harddisk",
        collection="volumes",
        resource_prefix="Volume",
        value_fn=lambda v: v.get("status", "unknown"),
    ),
    ZerobyteSensorEntityDescription(
        key="volume_type",
        translation_key="volume_type",
        name="Type",
        icon="mdi:folder-network",
        collection="volumes",
        resource_prefix="Volume",
        value_fn=lambda v: v.get("type", "unknown"),
    ),
)

# ---------------------------------------------------------------------------
# Repository sensors
# ---------------------------------------------------------------------------

REPOSITORY_SENSORS: tuple[ZerobyteSensorEntityDescription, ...] = (
    ZerobyteSensorEntityDescription(
        key="repo_status",
        translation_key="repo_status",
        name="Status",
        icon="mdi:database",
        collection="repositories",
        resource_prefix="Repository",
        value_fn=lambda r: r.get("status", "unknown"),
    ),
    ZerobyteSensorEntityDescription(
        key="repo_type",
        translation_key="repo_type",
        name="Type",
        icon="mdi:database-cog",
        collection="repositories",
        resource_prefix="Repository",
        value_fn=lambda r: r.get("type", "unknown"),
    ),
    ZerobyteSensorEntityDescription(
        key="repo_size",
        translation_key="repo_size",
        name="Size",
        icon="mdi:database-arrow-down",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_display_precision=1,
        collection="repositories",
        resource_prefix="Repository",
        value_fn=lambda r: r.get("stats", {}).get("total_size"),
    ),
    ZerobyteSensorEntityDescription(
        key="repo_snapshots",
        translation_key="repo_snapshots",
        name="Snapshots",
        icon="mdi:camera-burst",
        collection="repositories",
        resource_prefix="Repository",
        value_fn=lambda r: r.get("stats", {}).get("snapshots_count"),
    ),
)


# ---------------------------------------------------------------------------
# Platform setup
# ---------------------------------------------------------------------------


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZerobyteConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zerobyte sensor entities."""
    coordinator = entry.runtime_data.coordinator
    data = coordinator.data or {}
    entities: list[ZerobyteSensor] = []

    for item in data.get("backups", []):
        for desc in BACKUP_SENSORS:
            entities.append(
                ZerobyteSensor(coordinator, desc, item["shortId"], item["name"])
            )

    for item in data.get("volumes", []):
        for desc in VOLUME_SENSORS:
            entities.append(
                ZerobyteSensor(coordinator, desc, item["shortId"], item["name"])
            )

    for item in data.get("repositories", []):
        for desc in REPOSITORY_SENSORS:
            entities.append(
                ZerobyteSensor(coordinator, desc, item["shortId"], item["name"])
            )

    async_add_entities(entities)


class ZerobyteSensor(ZerobyteEntity, SensorEntity):
    """A sensor for a Zerobyte resource."""

    entity_description: ZerobyteSensorEntityDescription

    def __init__(
        self,
        coordinator: ZerobyteDataUpdateCoordinator,
        description: ZerobyteSensorEntityDescription,
        short_id: str,
        item_name: str,
    ) -> None:
        self._short_id = short_id
        entity_key = f"{description.collection}_{short_id}_{description.key}"
        super().__init__(coordinator, entity_key)
        self.entity_description = description
        self._attr_name = f"{description.resource_prefix} - {item_name} {description.name}"

    def _find_item(self) -> dict[str, Any] | None:
        """Look up the item in coordinator data by shortId."""
        collection = self.entity_description.collection
        for item in (self.coordinator.data or {}).get(collection, []):
            if item.get("shortId") == self._short_id:
                return item
        return None

    @property
    def native_value(self) -> Any:
        item = self._find_item()
        if item is None:
            return None
        return self.entity_description.value_fn(item)

    @property
    def available(self) -> bool:
        return super().available and self._find_item() is not None
