"""Select platform for Ducobox Connectivity Board.

Exposes Enum-type node actions (e.g. SetVentilationState) as select
entities, and reads the current state from the coordinator data.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .model.utils import safe_get

import logging

_LOGGER = logging.getLogger(__name__)

# Maps action names to the info path where the current state can be read.
# Format: action_name → (module, key) to read from each node in /info/nodes.
_ACTION_STATE_MAP = {
    'SetVentilationState': ('Ventilation', 'State'),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ducobox select entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]['coordinator']

    mac_address = (
        safe_get(coordinator.data, "info", "General", "Lan", "Mac", "Val") or "unknown_mac"
    )
    device_id = mac_address.replace(":", "").lower() if mac_address else "unknown_mac"

    entities: list[SelectEntity] = []

    action_nodes = safe_get(coordinator.data, 'action_nodes', 'Nodes') or []
    for node in action_nodes:
        node_id = node['Node']
        node_type = safe_get(coordinator.data, 'mappings', 'node_id_to_type', node_id) or 'Unknown'
        mapped_node_name = safe_get(coordinator.data, 'mappings', 'node_id_to_name', node_id)
        node_name = f'{device_id}:{mapped_node_name}'

        node_device_id = f"{device_id}-{node_id}"
        node_device_info = DeviceInfo(
            identifiers={(DOMAIN, node_device_id)},
            name=node_name,
            manufacturer="Ducobox",
            model=node_type,
            via_device=(DOMAIN, device_id),
        )

        for action in node.get('Actions', []):
            # Only create select entities for Enum-type actions
            if 'Enum' not in action or not action.get('Enum'):
                continue

            action_name = action['Action']
            state_path = _ACTION_STATE_MAP.get(action_name)

            entities.append(
                DucoboxActionSelectEntity(
                    coordinator=coordinator,
                    node_id=node_id,
                    device_info=node_device_info,
                    unique_id=f"{node_device_id}-{action_name}",
                    options=action['Enum'],
                    action=action_name,
                    state_module=state_path[0] if state_path else None,
                    state_key=state_path[1] if state_path else None,
                    name=_humanize_action(action_name),
                )
            )

    async_add_entities(entities)


def _humanize_action(action: str) -> str:
    """Convert 'SetVentilationState' → 'Ventilation State'."""
    import re
    name = action
    if name.startswith('Set'):
        name = name[3:]
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', name)
    return name


class DucoboxActionSelectEntity(CoordinatorEntity, SelectEntity):
    """Representation of a Ducobox action select entity.

    Extends CoordinatorEntity so that the current state is automatically
    updated from the coordinator data on each poll cycle.
    """

    def __init__(self, coordinator, node_id, device_info, unique_id, options, action, state_module, state_key, name):
        super().__init__(coordinator)
        self._node_id = node_id
        self._action = action
        self._state_module = state_module
        self._state_key = state_key
        self._device_info = device_info
        self._attr_unique_id = unique_id
        self._attr_name = f"{device_info['name']} {name}"
        self._attr_options = options

    @property
    def device_info(self):
        return self._device_info

    @property
    def current_option(self) -> str | None:
        """Return the current selected option from coordinator data."""
        if self._state_module and self._state_key:
            nodes = self.coordinator.data.get('nodes', [])
            for node in nodes:
                if node.get('Node') == self._node_id:
                    val = safe_get(node, self._state_module, self._state_key, 'Val')
                    if val is not None and str(val) in self._attr_options:
                        return str(val)
                    return val
        return None

    @property
    def options(self) -> list[str]:
        return self._attr_options

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.coordinator.async_set_ventilation_state(self._node_id, option, self._action)
        await self.coordinator.async_request_refresh()
