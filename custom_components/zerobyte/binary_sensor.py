"""Binary sensor platform for the Zerobyte integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import ZerobyteDataUpdateCoordinator
from .data import ZerobyteConfigEntry
from .entity import ZerobyteEntity


@dataclass(frozen=True, kw_only=True)
class ZerobyteBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describe a Zerobyte binary sensor."""

    collection: str
    resource_prefix: str
    is_on_fn: Callable[[dict[str, Any]], bool | None]


# ---------------------------------------------------------------------------
# Descriptors
# ---------------------------------------------------------------------------

BACKUP_BINARY_SENSORS: tuple[ZerobyteBinarySensorEntityDescription, ...] = (
    ZerobyteBinarySensorEntityDescription(
        key="backup_enabled",
        translation_key="backup_enabled",
        name="Enabled",
        icon="mdi:calendar-check",
        device_class=BinarySensorDeviceClass.RUNNING,
        collection="backups",
        resource_prefix="Backup",
        is_on_fn=lambda b: b.get("enabled"),
    ),
)

VOLUME_BINARY_SENSORS: tuple[ZerobyteBinarySensorEntityDescription, ...] = (
    ZerobyteBinarySensorEntityDescription(
        key="volume_health",
        translation_key="volume_health",
        name="Health",
        icon="mdi:harddisk",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        collection="volumes",
        resource_prefix="Volume",
        is_on_fn=lambda v: v.get("status") == "mounted",
    ),
)

REPOSITORY_BINARY_SENSORS: tuple[ZerobyteBinarySensorEntityDescription, ...] = (
    ZerobyteBinarySensorEntityDescription(
        key="repo_health",
        translation_key="repo_health",
        name="Health",
        icon="mdi:database-check",
        device_class=BinarySensorDeviceClass.PROBLEM,
        collection="repositories",
        resource_prefix="Repository",
        # device_class PROBLEM: True means there IS a problem
        is_on_fn=lambda r: r.get("status") != "healthy",
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
    """Set up Zerobyte binary sensor entities."""
    coordinator = entry.runtime_data.coordinator
    data = coordinator.data or {}
    entities: list[ZerobyteBinarySensor] = []

    for item in data.get("backups", []):
        for desc in BACKUP_BINARY_SENSORS:
            entities.append(
                ZerobyteBinarySensor(
                    coordinator, desc, item["shortId"], item["name"]
                )
            )

    for item in data.get("volumes", []):
        for desc in VOLUME_BINARY_SENSORS:
            entities.append(
                ZerobyteBinarySensor(
                    coordinator, desc, item["shortId"], item["name"]
                )
            )

    for item in data.get("repositories", []):
        for desc in REPOSITORY_BINARY_SENSORS:
            entities.append(
                ZerobyteBinarySensor(
                    coordinator, desc, item["shortId"], item["name"]
                )
            )

    async_add_entities(entities)


class ZerobyteBinarySensor(ZerobyteEntity, BinarySensorEntity):
    """A binary sensor for a Zerobyte resource."""

    entity_description: ZerobyteBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: ZerobyteDataUpdateCoordinator,
        description: ZerobyteBinarySensorEntityDescription,
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
    def is_on(self) -> bool | None:
        item = self._find_item()
        if item is None:
            return None
        return self.entity_description.is_on_fn(item)

    @property
    def available(self) -> bool:
        return super().available and self._find_item() is not None
