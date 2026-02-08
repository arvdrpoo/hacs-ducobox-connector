"""Sensor definitions and auto-discovery for Ducobox devices.

This module uses a registry-based approach: known sensor keys have explicit
metadata (unit, device class, processing function). Unknown keys found in the
API response are auto-discovered with sensible defaults so that new node types
and sensor keys work out of the box.
"""

from .utils import (
    process_node_temperature,
    process_node_humidity,
    process_node_co2,
    process_node_iaq,
    process_temperature,
    process_speed,
    process_pressure,
    process_rssi,
    process_uptime,
    process_timefilterremain,
    process_bypass_position,
    safe_get,
    extract_val,
)

from collections.abc import Callable
from dataclasses import dataclass
import logging
from homeassistant.components.sensor import (
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfPressure,
    UnitOfTime,
    PERCENTAGE,
    CONCENTRATION_PARTS_PER_MILLION,
    REVOLUTIONS_PER_MINUTE,
)


_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True, kw_only=True)
class DucoboxSensorEntityDescription(SensorEntityDescription):
    """Describes a Ducobox (box-level) sensor entity."""

    value_fn: Callable[[dict], float | None]
    data_path: tuple[str, ...] | None = None


@dataclass(frozen=True, kw_only=True)
class DucoboxNodeSensorEntityDescription(SensorEntityDescription):
    """Describes a Ducobox node sensor entity."""

    value_fn: Callable[[dict], float | None]
    sensor_key: str
    data_path: tuple[str, ...] | None = None


# ---------------------------------------------------------------------------
# Box-level sensors  (/info)
#
# These are checked for existence via data_path so only sensors actually
# present in the API response are registered.
# ---------------------------------------------------------------------------

SENSORS: tuple[DucoboxSensorEntityDescription, ...] = (
    # -- Ventilation / Sensor temperatures --
    # Documentation: https://www.duco.eu/Wes/CDN/1/Attachments/installation-guide-DucoBox-Energy-Comfort-(Plus)-(en)_638635518879333838.pdf
    # Oda = outdoor air → box
    DucoboxSensorEntityDescription(
        key="TempOda",
        name="Outdoor Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda data: process_temperature(
            safe_get(data, 'info', 'Ventilation', 'Sensor', 'TempOda', 'Val')
        ),
        data_path=('info', 'Ventilation', 'Sensor', 'TempOda'),
    ),
    # Sup = box → house (supply)
    DucoboxSensorEntityDescription(
        key="TempSup",
        name="Supply Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda data: process_temperature(
            safe_get(data, 'info', 'Ventilation', 'Sensor', 'TempSup', 'Val')
        ),
        data_path=('info', 'Ventilation', 'Sensor', 'TempSup'),
    ),
    # Eta = house → box (extract)
    DucoboxSensorEntityDescription(
        key="TempEta",
        name="Extract Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda data: process_temperature(
            safe_get(data, 'info', 'Ventilation', 'Sensor', 'TempEta', 'Val')
        ),
        data_path=('info', 'Ventilation', 'Sensor', 'TempEta'),
    ),
    # Eha = box → outdoor (exhaust)
    DucoboxSensorEntityDescription(
        key="TempEha",
        name="Exhaust Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda data: process_temperature(
            safe_get(data, 'info', 'Ventilation', 'Sensor', 'TempEha', 'Val')
        ),
        data_path=('info', 'Ventilation', 'Sensor', 'TempEha'),
    ),

    # -- Fan speeds --
    DucoboxSensorEntityDescription(
        key="SpeedSup",
        name="Supply Fan Speed",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: process_speed(
            safe_get(data, 'info', 'Ventilation', 'Fan', 'SpeedSup', 'Val')
        ),
        data_path=('info', 'Ventilation', 'Fan', 'SpeedSup'),
    ),
    DucoboxSensorEntityDescription(
        key="SpeedEha",
        name="Exhaust Fan Speed",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: process_speed(
            safe_get(data, 'info', 'Ventilation', 'Fan', 'SpeedEha', 'Val')
        ),
        data_path=('info', 'Ventilation', 'Fan', 'SpeedEha'),
    ),

    # -- Fan pressures --
    DucoboxSensorEntityDescription(
        key="PressSup",
        name="Supply Pressure",
        native_unit_of_measurement=UnitOfPressure.PA,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.PRESSURE,
        value_fn=lambda data: process_pressure(
            safe_get(data, 'info', 'Ventilation', 'Fan', 'PressSup', 'Val')
        ),
        data_path=('info', 'Ventilation', 'Fan', 'PressSup'),
    ),
    DucoboxSensorEntityDescription(
        key="PressEha",
        name="Exhaust Pressure",
        native_unit_of_measurement=UnitOfPressure.PA,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.PRESSURE,
        value_fn=lambda data: process_pressure(
            safe_get(data, 'info', 'Ventilation', 'Fan', 'PressEha', 'Val')
        ),
        data_path=('info', 'Ventilation', 'Fan', 'PressEha'),
    ),

    # -- Fan PWM --
    DucoboxSensorEntityDescription(
        key="PwmSup",
        name="Supply Fan PWM",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: safe_get(data, 'info', 'Ventilation', 'Fan', 'PwmSup', 'Val'),
        data_path=('info', 'Ventilation', 'Fan', 'PwmSup'),
    ),
    DucoboxSensorEntityDescription(
        key="PwmEha",
        name="Exhaust Fan PWM",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: safe_get(data, 'info', 'Ventilation', 'Fan', 'PwmEha', 'Val'),
        data_path=('info', 'Ventilation', 'Fan', 'PwmEha'),
    ),

    # -- Pressure targets --
    DucoboxSensorEntityDescription(
        key="PressSupTgt",
        name="Supply Pressure Target",
        native_unit_of_measurement=UnitOfPressure.PA,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.PRESSURE,
        value_fn=lambda data: process_pressure(
            safe_get(data, 'info', 'Ventilation', 'Fan', 'PressSupTgt', 'Val')
        ),
        data_path=('info', 'Ventilation', 'Fan', 'PressSupTgt'),
    ),
    DucoboxSensorEntityDescription(
        key="PressEhaTgt",
        name="Exhaust Pressure Target",
        native_unit_of_measurement=UnitOfPressure.PA,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.PRESSURE,
        value_fn=lambda data: process_pressure(
            safe_get(data, 'info', 'Ventilation', 'Fan', 'PressEhaTgt', 'Val')
        ),
        data_path=('info', 'Ventilation', 'Fan', 'PressEhaTgt'),
    ),

    # -- Wi-Fi signal strength --
    DucoboxSensorEntityDescription(
        key="RssiWifi",
        name="Wi-Fi Signal Strength",
        native_unit_of_measurement="dBm",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        value_fn=lambda data: process_rssi(
            safe_get(data, 'info', 'General', 'Lan', 'RssiWifi', 'Val')
        ),
        data_path=('info', 'General', 'Lan', 'RssiWifi'),
    ),

    # -- Device uptime --
    DucoboxSensorEntityDescription(
        key="UpTime",
        name="Device Uptime",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        value_fn=lambda data: process_uptime(
            safe_get(data, 'info', 'General', 'Board', 'UpTime', 'Val')
        ),
        data_path=('info', 'General', 'Board', 'UpTime'),
    ),

    # -- Heat recovery --
    DucoboxSensorEntityDescription(
        key="TimeFilterRemain",
        name="Filter Time Remaining",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DURATION,
        value_fn=lambda data: process_timefilterremain(
            safe_get(data, 'info', 'HeatRecovery', 'General', 'TimeFilterRemain', 'Val')
        ),
        data_path=('info', 'HeatRecovery', 'General', 'TimeFilterRemain'),
    ),
    DucoboxSensorEntityDescription(
        key="BypassPos",
        name="Bypass Position",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: process_bypass_position(
            safe_get(data, 'info', 'HeatRecovery', 'Bypass', 'Pos', 'Val')
        ),
        data_path=('info', 'HeatRecovery', 'Bypass', 'Pos'),
    ),
    DucoboxSensorEntityDescription(
        key="BypassTempSupTgt",
        name="Bypass Supply Temperature Target",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda data: process_temperature(
            safe_get(data, 'info', 'HeatRecovery', 'Bypass', 'TempSupTgt', 'Val')
        ),
        data_path=('info', 'HeatRecovery', 'Bypass', 'TempSupTgt'),
    ),

    # -- Frost protection --
    DucoboxSensorEntityDescription(
        key="FrostProtectState",
        name="Frost Protection State",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: safe_get(data, 'info', 'HeatRecovery', 'ProtectFrost', 'State', 'Val'),
        data_path=('info', 'HeatRecovery', 'ProtectFrost', 'State'),
    ),
    DucoboxSensorEntityDescription(
        key="FrostProtectPressReduct",
        name="Frost Protection Pressure Reduction",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: safe_get(data, 'info', 'HeatRecovery', 'ProtectFrost', 'PressReduct', 'Val'),
        data_path=('info', 'HeatRecovery', 'ProtectFrost', 'PressReduct'),
    ),

    # -- NightBoost --
    DucoboxSensorEntityDescription(
        key="NightBoostTempOutsideAvg",
        name="NightBoost Outside Temperature Average",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda data: process_temperature(
            safe_get(data, 'info', 'NightBoost', 'General', 'TempOutsideAvg', 'Val')
        ),
        data_path=('info', 'NightBoost', 'General', 'TempOutsideAvg'),
    ),
    DucoboxSensorEntityDescription(
        key="NightBoostFlowLvlReqZone1",
        name="NightBoost Flow Level Request Zone 1",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: safe_get(data, 'info', 'NightBoost', 'General', 'FlowLvlReqZone1', 'Val'),
        data_path=('info', 'NightBoost', 'General', 'FlowLvlReqZone1'),
    ),

    # -- VentCool --
    DucoboxSensorEntityDescription(
        key="VentCoolState",
        name="Ventilation Cooling State",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: safe_get(data, 'info', 'VentCool', 'General', 'State', 'Val'),
        data_path=('info', 'VentCool', 'General', 'State'),
    ),
    DucoboxSensorEntityDescription(
        key="VentCoolTempInside",
        name="Ventilation Cooling Inside Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda data: process_temperature(
            safe_get(data, 'info', 'VentCool', 'General', 'TempInside', 'Val')
        ),
        data_path=('info', 'VentCool', 'General', 'TempInside'),
    ),

    # -- Diagnostics --
    DucoboxSensorEntityDescription(
        key="DiagStatus",
        name="Diagnostic Status",
        value_fn=lambda data: (ss[0].get('Status') if (ss := safe_get(data, 'info', 'Diag', 'SubSystems')) and isinstance(ss, list) and len(ss) > 0 else None),
        data_path=('info', 'Diag', 'SubSystems'),
    ),
)


# ---------------------------------------------------------------------------
# Node-level sensor auto-discovery
#
# Instead of hard-coding sensors per node type (BOX, UCCO2, BSRH, …),
# we define a *registry* of known sensor keys with their metadata.
# At setup time, sensor.py iterates the actual node data and creates
# entities for every key found, looking up metadata from this registry.
# Unknown keys get sensible defaults — no code changes needed for new
# node types or new sensor keys.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NodeSensorMeta:
    """Metadata for a known node sensor key."""

    name: str
    native_unit_of_measurement: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = SensorStateClass.MEASUREMENT
    process_fn: Callable[[float | None], float | None] | None = None
    icon: str | None = None


# Registry: module → key → metadata
# The module corresponds to the top-level key in the node dict
# (e.g. "Sensor", "Ventilation", "NetworkDuco").
NODE_SENSOR_REGISTRY: dict[str, dict[str, NodeSensorMeta]] = {
    'Sensor': {
        'Temp': NodeSensorMeta(
            name='Temperature',
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            process_fn=process_node_temperature,
        ),
        'Rh': NodeSensorMeta(
            name='Relative Humidity',
            native_unit_of_measurement=PERCENTAGE,
            device_class=SensorDeviceClass.HUMIDITY,
            process_fn=process_node_humidity,
        ),
        'IaqRh': NodeSensorMeta(
            name='Humidity Air Quality',
            native_unit_of_measurement=PERCENTAGE,
            process_fn=process_node_iaq,
            icon='mdi:air-filter',
        ),
        'Co2': NodeSensorMeta(
            name='CO₂',
            native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
            device_class=SensorDeviceClass.CO2,
            process_fn=process_node_co2,
        ),
        'IaqCo2': NodeSensorMeta(
            name='CO₂ Air Quality',
            native_unit_of_measurement=PERCENTAGE,
            process_fn=process_node_iaq,
            icon='mdi:air-filter',
        ),
    },
    'Ventilation': {
        'State': NodeSensorMeta(
            name='Ventilation State',
            state_class=None,
            icon='mdi:hvac',
        ),
        'Mode': NodeSensorMeta(
            name='Ventilation Mode',
            state_class=None,
            icon='mdi:hvac',
        ),
        'FlowLvlTgt': NodeSensorMeta(
            name='Flow Level Target',
            native_unit_of_measurement=PERCENTAGE,
            icon='mdi:fan',
        ),
        'TimeStateRemain': NodeSensorMeta(
            name='Time State Remaining',
            native_unit_of_measurement=UnitOfTime.SECONDS,
            icon='mdi:timer-outline',
        ),
        'TimeStateEnd': NodeSensorMeta(
            name='Time State End',
            native_unit_of_measurement=UnitOfTime.SECONDS,
            icon='mdi:timer-outline',
        ),
        'Pos': NodeSensorMeta(
            name='Valve Position',
            native_unit_of_measurement=PERCENTAGE,
            icon='mdi:valve',
        ),
        'FlowLvlOvrl': NodeSensorMeta(
            name='Flow Level Override',
            native_unit_of_measurement=PERCENTAGE,
            icon='mdi:fan',
        ),
        'FlowLvlReqSensor': NodeSensorMeta(
            name='Flow Level Sensor Request',
            native_unit_of_measurement=PERCENTAGE,
            icon='mdi:fan',
        ),
    },
    'NetworkDuco': {
        'CommErrorCtr': NodeSensorMeta(
            name='Communication Error Counter',
            state_class=SensorStateClass.TOTAL_INCREASING,
            icon='mdi:alert-circle-outline',
        ),
        'RssiRfN2M': NodeSensorMeta(
            name='RF Signal Strength (Node to Master)',
            native_unit_of_measurement='dBm',
            device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        ),
        'RssiRfN2H': NodeSensorMeta(
            name='RF Signal Strength (Node to Hub)',
            native_unit_of_measurement='dBm',
            device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        ),
        'HopRf': NodeSensorMeta(
            name='RF Hop Count',
            icon='mdi:access-point-network',
        ),
    },
}


def _humanize_key(key: str) -> str:
    """Convert a CamelCase key to a human-readable name.

    E.g. 'FlowLvlTgt' -> 'Flow Lvl Tgt'
    """
    import re
    # Insert space before uppercase letters that follow lowercase letters
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', key)
    # Insert space before uppercase letters followed by lowercase (handles acronyms)
    name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', name)
    return name


def discover_node_sensors(
    node: dict,
) -> list[DucoboxNodeSensorEntityDescription]:
    """Auto-discover sensors from a node's data dict.

    Iterates modules (Sensor, Ventilation, NetworkDuco) and creates
    entity descriptions for every key that has a {'Val': ...} value.
    Known keys get rich metadata from NODE_SENSOR_REGISTRY;
    unknown keys get sensible defaults.
    """
    descriptions: list[DucoboxNodeSensorEntityDescription] = []
    modules_to_scan = ('Sensor', 'Ventilation', 'NetworkDuco')

    for module in modules_to_scan:
        module_data = node.get(module)
        if not isinstance(module_data, dict):
            continue

        registry = NODE_SENSOR_REGISTRY.get(module, {})

        for key, value in module_data.items():
            # Only consider keys whose value is a dict with 'Val'
            if not isinstance(value, dict) or 'Val' not in value:
                continue

            meta = registry.get(key)
            sensor_key = f"{module}_{key}"

            if meta is not None:
                # Known sensor — use rich metadata
                name = meta.name
                unit = meta.native_unit_of_measurement
                device_class = meta.device_class
                state_class = meta.state_class
                icon = meta.icon
                process_fn = meta.process_fn

                if process_fn is not None:
                    value_fn = _make_value_fn_processed(module, key, process_fn)
                else:
                    value_fn = _make_value_fn_raw(module, key)
            else:
                # Unknown sensor — auto-discover with defaults
                name = f"{module} {_humanize_key(key)}"
                unit = None
                device_class = None
                state_class = SensorStateClass.MEASUREMENT
                icon = None
                value_fn = _make_value_fn_raw(module, key)

                _LOGGER.info(
                    "Auto-discovered unknown node sensor: module=%s key=%s "
                    "in node %s (type=%s). Consider adding it to NODE_SENSOR_REGISTRY.",
                    module, key,
                    node.get('Node'),
                    safe_get(node, 'General', 'Type', 'Val'),
                )

            kwargs = dict(
                key=sensor_key,
                name=name,
                value_fn=value_fn,
                sensor_key=sensor_key,
                data_path=(module, key),
            )
            if unit is not None:
                kwargs['native_unit_of_measurement'] = unit
            if device_class is not None:
                kwargs['device_class'] = device_class
            if state_class is not None:
                kwargs['state_class'] = state_class
            if icon is not None:
                kwargs['icon'] = icon

            descriptions.append(DucoboxNodeSensorEntityDescription(**kwargs))

    return descriptions


def _make_value_fn_processed(
    module: str, key: str, process_fn: Callable
) -> Callable[[dict], float | None]:
    """Create a value_fn that extracts Val and applies a processing function."""
    def value_fn(node: dict) -> float | None:
        raw = safe_get(node, module, key)
        return process_fn(extract_val(raw))
    return value_fn


def _make_value_fn_raw(
    module: str, key: str
) -> Callable[[dict], float | None]:
    """Create a value_fn that just extracts the Val."""
    def value_fn(node: dict) -> float | None:
        raw = safe_get(node, module, key)
        return extract_val(raw)
    return value_fn
