"""Select platform for Ducobox Connectivity Board.

Exposes Enum-type node actions (e.g. SetVentilationState) as select
entities, and box-level config parameters that behave as enums
(e.g. HeatRecovery.Bypass.Mode) as select entities with human-readable
option labels.
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
from .number import _humanize_config_key

import logging
import re

_LOGGER = logging.getLogger(__name__)

# Maps action names to the info path where the current state can be read.
# Format: action_name → (module, key) to read from each node in /info/nodes.
_ACTION_STATE_MAP = {
    'SetVentilationState': ('Ventilation', 'State'),
}

# ── Box-level config parameters that are selects ──
# (module, submodule, key) → list of (api_value, label) pairs.
_CONFIG_SELECT_PARAMS: dict[tuple[str, str, str], list[tuple[int, str]]] = {
    ('HeatRecovery', 'Bypass', 'Mode'): [
        (0, 'Auto'),
        (1, 'Closed'),
        (2, 'Open'),
    ],
    ('VentCool', 'General', 'Mode'): [
        (0, 'Off'),
        (1, 'Auto'),
        (2, 'On'),
    ],
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

    # ── Box-level config select entities ──
    box_name = safe_get(coordinator.data, "info", "General", "Board", "BoxName", "Val") or "Unknown Model"
    box_subtype = safe_get(coordinator.data, "info", "General", "Board", "BoxSubTypeName", "Val") or ""
    box_model = f"{box_name} {box_subtype}".replace('_', ' ').strip()

    box_device_info = DeviceInfo(
        identifiers={(DOMAIN, device_id)},
        name=device_id,
        manufacturer="Ducobox",
        model=box_model,
        sw_version=safe_get(coordinator.data, "info", "General", "Board", "SwVersionBox", "Val") or "Unknown Version",
    )

    box_config = coordinator.data.get('config', {})
    for (module, submodule, key), option_pairs in _CONFIG_SELECT_PARAMS.items():
        value = safe_get(box_config, module, submodule, key)
        if value is None:
            continue
        labels = [label for _, label in option_pairs]
        val_to_label = {v: label for v, label in option_pairs}
        label_to_val = {label: v for v, label in option_pairs}

        readable_name = f"{module} {submodule} {_humanize_config_key(key)}"
        unique_id = f"{device_id}-config-{module}-{submodule}-{key}"
        entities.append(
            DucoboxConfigSelectEntity(
                coordinator=coordinator,
                module=module,
                submodule=submodule,
                param_key=key,
                device_info=box_device_info,
                unique_id=unique_id,
                name=readable_name,
                options=labels,
                val_to_label=val_to_label,
                label_to_val=label_to_val,
            )
        )

    async_add_entities(entities)


def _humanize_action(action: str) -> str:
    """Convert 'SetVentilationState' → 'Ventilation State'."""
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


class DucoboxConfigSelectEntity(CoordinatorEntity, SelectEntity):
    """Representation of a box-level config parameter with a fixed set of options.

    Maps integer API values (0, 1, 2 …) to human-readable labels.
    """

    def __init__(self, coordinator, module, submodule, param_key, device_info, unique_id, name, options, val_to_label, label_to_val):
        super().__init__(coordinator)
        self._module = module
        self._submodule = submodule
        self._param_key = param_key
        self._device_info = device_info
        self._val_to_label = val_to_label
        self._label_to_val = label_to_val
        self._attr_unique_id = unique_id
        self._attr_name = f"{device_info['name']} {name}"
        self._attr_options = options

    @property
    def device_info(self):
        return self._device_info

    @property
    def current_option(self) -> str | None:
        """Return the current selected option from coordinator data."""
        raw = safe_get(
            self.coordinator.data, 'config',
            self._module, self._submodule, self._param_key, 'Val'
        )
        if raw is not None:
            return self._val_to_label.get(raw)
        return None

    @property
    def options(self) -> list[str]:
        return self._attr_options

    async def async_select_option(self, option: str) -> None:
        """Change the selected option, converting label back to API int."""
        api_val = self._label_to_val[option]
        await self.coordinator.async_set_box_config(
            self._module, self._submodule, self._param_key, api_val
        )
        await self.coordinator.async_request_refresh()
