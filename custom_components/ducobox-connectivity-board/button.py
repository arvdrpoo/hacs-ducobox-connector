"""Button platform for Ducobox Connectivity Board.

Exposes safe box-level actions (like resetting filter timer, refreshing
node data, reconnecting Wi-Fi) as press-button entities in Home Assistant.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable, Coroutine
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .model.utils import safe_get
from .model.coordinator import DucoboxCoordinator

import logging

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class DucoboxButtonEntityDescription(ButtonEntityDescription):
    """Describes a Ducobox button entity."""

    action: str
    icon: str | None = None


# Safe box-level actions that are non-destructive
BOX_BUTTONS: tuple[DucoboxButtonEntityDescription, ...] = (
    DucoboxButtonEntityDescription(
        key="reset_filter_time_remain",
        name="Reset Filter Timer",
        action="ResetFilterTimeRemain",
        icon="mdi:air-filter",
    ),
    DucoboxButtonEntityDescription(
        key="update_node_data",
        name="Update Node Data",
        action="UpdateNodeData",
        icon="mdi:refresh",
    ),
    DucoboxButtonEntityDescription(
        key="reconnect_wifi",
        name="Reconnect Wi-Fi",
        action="ReconnectWifi",
        icon="mdi:wifi-sync",
    ),
    DucoboxButtonEntityDescription(
        key="scan_wifi",
        name="Scan Wi-Fi Networks",
        action="ScanWifi",
        icon="mdi:wifi-find",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ducobox button entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]['coordinator']

    mac_address = (
        safe_get(coordinator.data, "info", "General", "Lan", "Mac", "Val") or "unknown_mac"
    )

    if mac_address == 'unknown_mac':
        return

    device_id = mac_address.replace(":", "").lower()

    box_name = safe_get(coordinator.data, "info", "General", "Board", "BoxName", "Val") or "Unknown Model"
    box_subtype = safe_get(coordinator.data, "info", "General", "Board", "BoxSubTypeName", "Val") or ""
    box_model = f"{box_name} {box_subtype}".replace('_', ' ').strip()

    device_info = DeviceInfo(
        identifiers={(DOMAIN, device_id)},
        name=device_id,
        manufacturer="Ducobox",
        model=box_model,
        sw_version=safe_get(coordinator.data, "info", "General", "Board", "SwVersionBox", "Val") or "Unknown Version",
    )

    # Only create buttons for actions that actually exist in the API
    available_actions = set()
    box_actions = safe_get(coordinator.data, 'action', 'Actions') or []
    for act in box_actions:
        if isinstance(act, dict) and 'Action' in act:
            available_actions.add(act['Action'])

    entities: list[ButtonEntity] = []
    for description in BOX_BUTTONS:
        if description.action in available_actions:
            unique_id = f"{device_id}-{description.key}"
            entities.append(
                DucoboxButtonEntity(
                    coordinator=coordinator,
                    description=description,
                    device_info=device_info,
                    unique_id=unique_id,
                )
            )

    async_add_entities(entities)


class DucoboxButtonEntity(CoordinatorEntity, ButtonEntity):
    """Representation of a Ducobox button entity."""

    entity_description: DucoboxButtonEntityDescription

    def __init__(
        self,
        coordinator: DucoboxCoordinator,
        description: DucoboxButtonEntityDescription,
        device_info: DeviceInfo,
        unique_id: str,
    ) -> None:
        """Initialize a Ducobox button entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_device_info = device_info
        self._attr_unique_id = unique_id
        self._attr_name = f"{device_info['name']} {description.name}"
        if description.icon:
            self._attr_icon = description.icon

    @property
    def device_info(self):
        """Return the device info."""
        return self._attr_device_info

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_execute_action(self.entity_description.action)
