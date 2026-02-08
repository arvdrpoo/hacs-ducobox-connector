from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity

from .const import DOMAIN

from .model.utils import safe_get
from .model.devices import SENSORS, discover_node_sensors
from .model.coordinator import DucoboxCoordinator, DucoboxSensorEntity, DucoboxNodeSensorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ducobox sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]['coordinator']

    # Retrieve MAC address and format device ID and name
    mac_address = (
        safe_get(coordinator.data, "info", "General", "Lan", "Mac", "Val") or "unknown_mac"
    )

    if mac_address == 'unknown_mac':
        # if no data -> stop adding device
        return

    device_id = mac_address.replace(":", "").lower() if mac_address else "unknown_mac"
    device_name = f"{device_id}"

    box_name = safe_get(coordinator.data, "info", "General", "Board", "BoxName", "Val") or "Unknown Model"
    box_subtype = safe_get(coordinator.data, "info", "General", "Board", "BoxSubTypeName", "Val") or ""
    box_model = f"{box_name} {box_subtype}".replace('_', ' ').strip()

    device_info = DeviceInfo(
        identifiers={(DOMAIN, device_id)},
        name=device_name,
        manufacturer="Ducobox",
        model=box_model,
        sw_version=safe_get(coordinator.data, "info", "General", "Board", "SwVersionBox", "Val") or "Unknown Version",
    )

    entities: list[SensorEntity] = []

    # Add main Ducobox sensors (only if data exists)
    for description in SENSORS:
        # Check if sensor data exists
        if description.data_path is not None:
            if safe_get(coordinator.data, *description.data_path) is None:
                continue  # Skip sensor if data path doesn't exist

        unique_id = f"{device_id}-{description.key}"
        entities.append(
            DucoboxSensorEntity(
                coordinator=coordinator,
                description=description,
                device_info=device_info,
                unique_id=unique_id,
            )
        )

    # Add node sensors — auto-discovered from the actual API data
    nodes = safe_get(coordinator.data, 'nodes') or []
    for node in nodes:
        node_id = node.get('Node')
        node_type = safe_get(node, 'General', 'Type', 'Val') or 'Unknown'
        node_name = f"{device_id}:{node_id}:{node_type}"

        # Create device info for the node
        node_device_id = f"{device_id}-{node_id}"

        sw_version = safe_get(node, 'General', 'SwVersion', 'Val')
        serial = safe_get(node, 'General', 'SerialDuco', 'Val')

        node_device_info = DeviceInfo(
            identifiers={(DOMAIN, node_device_id)},
            name=node_name,
            manufacturer="Ducobox",
            model=node_type,
            sw_version=sw_version if sw_version and sw_version != 'n/a' else None,
            serial_number=serial if serial and serial != 'n/a' else None,
            via_device=(DOMAIN, device_id),
        )

        # Auto-discover sensors from the node's actual data
        node_descriptions = discover_node_sensors(node)
        for description in node_descriptions:
            unique_id = f"{node_device_id}-{description.key}"
            entities.append(
                DucoboxNodeSensorEntity(
                    coordinator=coordinator,
                    node_id=node_id,
                    description=description,
                    device_info=node_device_info,
                    unique_id=unique_id,
                    device_id=device_id,
                    node_name=node_name,
                )
            )

    async_add_entities(entities)
