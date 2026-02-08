"""Switch platform for Ducobox Connectivity Board.

Auto-discovers boolean (Min=0, Max=1) config parameters from the
box-level /config API endpoint and exposes them as HA switch entities.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .model.utils import safe_get
from .number import _is_number_param, _humanize_config_key, _box_config_skip, _box_config_skip_keys

import logging

_LOGGER = logging.getLogger(__name__)


def _is_boolean_param(value) -> bool:
    """A {Val, Min, Max, Inc} param is boolean when Min=0 and Max=1."""
    return (
        _is_number_param(value)
        and value['Min'] == 0
        and value['Max'] == 1
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ducobox switches from a config entry."""
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

    entities = []

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
                if not _is_boolean_param(value):
                    continue
                if (module, submodule, key) in _box_config_skip_keys:
                    continue

                readable_name = f"{module} {submodule} {_humanize_config_key(key)}"
                unique_id = f"{device_id}-config-{module}-{submodule}-{key}"
                entities.append(
                    DucoboxBoxSwitchEntity(
                        coordinator=coordinator,
                        module=module,
                        submodule=submodule,
                        param_key=key,
                        device_info=device_info,
                        unique_id=unique_id,
                        name=readable_name,
                    )
                )

    async_add_entities(entities)


class DucoboxBoxSwitchEntity(CoordinatorEntity, SwitchEntity):
    """Representation of a box-level boolean config parameter as a switch."""

    def __init__(self, coordinator, module, submodule, param_key, device_info, unique_id, name):
        super().__init__(coordinator)
        self._module = module
        self._submodule = submodule
        self._param_key = param_key
        self._device_info = device_info
        self._attr_unique_id = unique_id
        self._attr_name = f"{device_info['name']} {name}"

    @property
    def device_info(self):
        return self._device_info

    @property
    def is_on(self) -> bool | None:
        """Read current value from coordinator data."""
        raw = safe_get(
            self.coordinator.data, 'config',
            self._module, self._submodule, self._param_key, 'Val'
        )
        if raw is not None:
            return bool(raw)
        return None

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_box_config(
            self._module, self._submodule, self._param_key, 1
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_box_config(
            self._module, self._submodule, self._param_key, 0
        )
        await self.coordinator.async_request_refresh()
