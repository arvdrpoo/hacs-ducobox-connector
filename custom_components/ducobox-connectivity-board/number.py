"""Number platform for Ducobox Connectivity Board.

Auto-discovers configurable parameters from both box-level (/config)
and node-level (/config/nodes) API endpoints. Any parameter with the
structure {Val, Min, Max, Inc} becomes a NumberEntity.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .model.utils import safe_get
from .model.coordinator import DucoboxCoordinator

import logging
import re

_LOGGER = logging.getLogger(__name__)


def _is_number_param(value) -> bool:
    """Check if a value is a configurable number parameter ({Val, Min, Max, Inc})."""
    return (
        isinstance(value, dict)
        and 'Val' in value
        and 'Min' in value
        and 'Max' in value
        and 'Inc' in value
    )


def _humanize_config_key(key: str) -> str:
    """Convert a CamelCase config key to a human-readable name."""
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', key)
    name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', name)
    return name


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ducobox numbers from a config entry."""
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

    entities: list[NumberEntity] = []

    # ── Box-level number entities from /config ──
    #
    # Skip parameters that are:
    #  - Fixed (Min == Max): user can't change them, e.g. Setup.Complete
    #  - Internal/dangerous: Modbus addresses, reboot schedules, firmware,
    #    Azure, daily counters, etc.
    _box_config_skip = frozenset({
        ('General', 'Setup'),             # Complete, Language, Country — setup wizard params
        ('General', 'Modbus'),            # Addr, Offset, DailyWriteReqCnt — bus config
        ('General', 'AutoRebootComm'),    # Period, Time — auto-reboot scheduling
        ('General', 'PublicApi'),         # DailyWriteReqCnt — internal counter
        ('Firmware', 'General'),          # DowngradeAllow — dangerous
        ('Azure', 'Connection'),          # Enable — cloud connectivity toggle
    })

    # Individual keys to skip (module, submodule, key)
    _box_config_skip_keys = frozenset({
        ('General', 'Lan', 'Mode'),              # Network mode enum — not a tunable number
        ('General', 'Lan', 'Dhcp'),              # Boolean flag — not a tunable number
        ('General', 'Lan', 'TimeDucoClientIp'),  # Internal timing for Duco client
    })

    box_config = coordinator.data.get('config', {})
    for module, module_data in box_config.items():
        if not isinstance(module_data, dict):
            continue
        for submodule, sub_data in module_data.items():
            if not isinstance(sub_data, dict):
                continue
            if (module, submodule) in _box_config_skip:
                continue
            for key, value in sub_data.items():
                if not _is_number_param(value):
                    continue
                # Skip fixed params where Min == Max (not user-configurable)
                if value['Min'] == value['Max']:
                    continue
                # Skip individually excluded keys
                if (module, submodule, key) in _box_config_skip_keys:
                    continue
                readable_name = f"{module} {submodule} {_humanize_config_key(key)}"
                unique_id = f"{device_id}-config-{module}-{submodule}-{key}"
                entities.append(
                        DucoboxBoxNumberEntity(
                            coordinator=coordinator,
                            module=module,
                            submodule=submodule,
                            param_key=key,
                            device_info=device_info,
                            unique_id=unique_id,
                            name=readable_name,
                            min_value=value['Min'],
                            max_value=value['Max'],
                            step=value['Inc'],
                        )
                    )

    # ── Node-level number entities from /config/nodes ──
    number_nodes = safe_get(coordinator.data, 'config_nodes', 'Nodes') or []
    for node in number_nodes:
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

        for key, value in node.items():
            if _is_number_param(value):
                unique_id = f"{node_device_id}-{key}"
                entities.append(
                    DucoboxNodeNumberEntity(
                        coordinator=coordinator,
                        node_id=node_id,
                        param_key=key,
                        device_info=node_device_info,
                        unique_id=unique_id,
                        min_value=int(value['Min']),
                        max_value=int(value['Max']),
                        step=int(value['Inc']),
                    )
                )

    async_add_entities(entities)


class DucoboxNodeNumberEntity(CoordinatorEntity, NumberEntity):
    """Representation of a node-level Ducobox number entity.

    Reads its current value from coordinator.data['config_nodes'] on every
    poll cycle.
    """

    def __init__(self, coordinator, node_id, param_key, device_info, unique_id, min_value, max_value, step):
        super().__init__(coordinator)
        self._node_id = node_id
        self._param_key = param_key
        self._device_info = device_info
        self._attr_unique_id = unique_id
        self._attr_name = f"{device_info['name']} {_humanize_config_key(param_key)}"
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_mode = NumberMode.AUTO

    @property
    def device_info(self):
        return self._device_info

    @property
    def native_value(self):
        """Read current value from the coordinator data (polled every cycle)."""
        nodes = safe_get(self.coordinator.data, 'config_nodes', 'Nodes') or []
        for node in nodes:
            if node.get('Node') == self._node_id:
                param = node.get(self._param_key)
                if isinstance(param, dict) and 'Val' in param:
                    return param['Val']
        return None

    async def async_set_native_value(self, value: float):
        await self.coordinator.async_set_value(self._node_id, self._param_key, value)
        await self.coordinator.async_request_refresh()


class DucoboxBoxNumberEntity(CoordinatorEntity, NumberEntity):
    """Representation of a box-level Ducobox number entity.

    Reads its current value from coordinator.data['config'] on every
    poll cycle.
    """

    def __init__(self, coordinator, module, submodule, param_key, device_info, unique_id, name, min_value, max_value, step):
        super().__init__(coordinator)
        self._module = module
        self._submodule = submodule
        self._param_key = param_key
        self._device_info = device_info
        self._attr_unique_id = unique_id
        self._attr_name = f"{device_info['name']} {name}"
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_mode = NumberMode.AUTO

    @property
    def device_info(self):
        return self._device_info

    @property
    def native_value(self):
        """Read current value from the coordinator data (polled every cycle)."""
        return safe_get(
            self.coordinator.data, 'config',
            self._module, self._submodule, self._param_key, 'Val'
        )

    async def async_set_native_value(self, value: float):
        # Determine if value should be int or float based on step
        if self._attr_native_step and self._attr_native_step == int(self._attr_native_step):
            value = int(round(value))
        await self.coordinator.async_set_box_config(
            self._module, self._submodule, self._param_key, value
        )
        await self.coordinator.async_request_refresh()
