"""Shared test fixtures and Home Assistant mock infrastructure.

Testing a HACS / Home Assistant custom component without a full HA install
requires stubbing out the ``homeassistant`` package.  We inject lightweight
fakes into ``sys.modules`` *before* any integration code is imported so that
all ``from homeassistant.… import …`` statements resolve normally.

This approach lets us test the real business logic (data processing, sensor
auto-discovery, coordinator data flow) without pulling in the entire HA core.
"""

from __future__ import annotations

import sys
import types
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from unittest.mock import AsyncMock, MagicMock
import pytest


# ───────────────────────────────────────────────────────────────────────
# 1.  Lightweight HA stubs
# ───────────────────────────────────────────────────────────────────────

# --- homeassistant.const ---
_ha_const = types.ModuleType("homeassistant.const")
_ha_const.UnitOfTemperature = type("UnitOfTemperature", (), {"CELSIUS": "°C", "FAHRENHEIT": "°F"})
_ha_const.UnitOfPressure = type("UnitOfPressure", (), {"PA": "Pa", "HPA": "hPa"})
_ha_const.UnitOfTime = type("UnitOfTime", (), {"SECONDS": "s", "MINUTES": "min", "HOURS": "h", "DAYS": "d"})
_ha_const.PERCENTAGE = "%"
_ha_const.CONCENTRATION_PARTS_PER_MILLION = "ppm"
_ha_const.REVOLUTIONS_PER_MINUTE = "rpm"


# --- homeassistant.components.sensor ---
class _SensorStateClass(str, Enum):
    MEASUREMENT = "measurement"
    TOTAL = "total"
    TOTAL_INCREASING = "total_increasing"


class _SensorDeviceClass(str, Enum):
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    CO2 = "carbon_dioxide"
    SIGNAL_STRENGTH = "signal_strength"
    DURATION = "duration"


@dataclass(frozen=True, kw_only=True)
class _SensorEntityDescription:
    key: str
    name: str | None = None
    native_unit_of_measurement: str | None = None
    device_class: _SensorDeviceClass | None = None
    state_class: _SensorStateClass | None = None
    icon: str | None = None


class _SensorEntity:
    entity_description: Any = None


_ha_sensor = types.ModuleType("homeassistant.components.sensor")
_ha_sensor.SensorEntityDescription = _SensorEntityDescription
_ha_sensor.SensorDeviceClass = _SensorDeviceClass
_ha_sensor.SensorStateClass = _SensorStateClass
_ha_sensor.SensorEntity = _SensorEntity

_ha_components = types.ModuleType("homeassistant.components")

# --- homeassistant.helpers.update_coordinator ---
class _CoordinatorEntity:
    def __init__(self, coordinator, *args, **kwargs):
        self.coordinator = coordinator

    def __class_getitem__(cls, item):
        """Support CoordinatorEntity[T] generic syntax."""
        return cls


class _DataUpdateCoordinator:
    def __init__(self, hass, logger, *, name, update_interval):
        self.hass = hass
        self.name = name
        self.update_interval = update_interval
        self.data = {}
        self.last_update_success = True


class _UpdateFailed(Exception):
    pass


_ha_update_coord = types.ModuleType("homeassistant.helpers.update_coordinator")
_ha_update_coord.CoordinatorEntity = _CoordinatorEntity
_ha_update_coord.DataUpdateCoordinator = _DataUpdateCoordinator
_ha_update_coord.UpdateFailed = _UpdateFailed

# --- homeassistant.helpers.device_registry ---
_ha_device_registry = types.ModuleType("homeassistant.helpers.device_registry")
_ha_device_registry.DeviceInfo = dict  # DeviceInfo is basically a TypedDict

# --- homeassistant.helpers.entity_platform ---
_ha_entity_platform = types.ModuleType("homeassistant.helpers.entity_platform")
_ha_entity_platform.AddEntitiesCallback = Any

# --- homeassistant.config_entries ---
_ha_config_entries = types.ModuleType("homeassistant.config_entries")
_ha_config_entries.ConfigEntry = MagicMock
_ha_config_entries.ConfigEntryNotReady = type("ConfigEntryNotReady", (Exception,), {})

# --- homeassistant.core ---
_ha_core = types.ModuleType("homeassistant.core")
_ha_core.HomeAssistant = MagicMock
_ha_core.callback = lambda fn: fn

# --- homeassistant.helpers ---
_ha_helpers = types.ModuleType("homeassistant.helpers")

# --- homeassistant.helpers.service_info ---
_ha_helpers_service_info = types.ModuleType("homeassistant.helpers.service_info")

# --- homeassistant.helpers.service_info.zeroconf ---
_ha_helpers_zeroconf = types.ModuleType("homeassistant.helpers.service_info.zeroconf")
_ha_helpers_zeroconf.ZeroconfServiceInfo = MagicMock

# --- homeassistant.data_entry_flow ---
_ha_data_entry_flow = types.ModuleType("homeassistant.data_entry_flow")
_ha_data_entry_flow.FlowResult = dict

# --- homeassistant.helpers.selector ---
_ha_helpers_selector = types.ModuleType("homeassistant.helpers.selector")
_ha_helpers_selector.TextSelector = MagicMock
_ha_helpers_selector.TextSelectorConfig = MagicMock

# --- homeassistant.components.number ---
_ha_number = types.ModuleType("homeassistant.components.number")
_ha_number.NumberEntity = type("NumberEntity", (), {})
_ha_number.NumberMode = type("NumberMode", (), {"AUTO": "auto", "BOX": "box", "SLIDER": "slider"})

# --- homeassistant.components.button ---
@dataclass(frozen=True, kw_only=True)
class _ButtonEntityDescription:
    key: str
    name: str | None = None
    icon: str | None = None

_ha_button = types.ModuleType("homeassistant.components.button")
_ha_button.ButtonEntity = type("ButtonEntity", (), {})
_ha_button.ButtonEntityDescription = _ButtonEntityDescription

# --- homeassistant.components.select ---
_ha_select = types.ModuleType("homeassistant.components.select")
_ha_select.SelectEntity = type("SelectEntity", (), {})


# ───────────────────────────────────────────────────────────────────────
# 2.  Register stubs in sys.modules  (before any import of custom_components)
# ───────────────────────────────────────────────────────────────────────

_stubs = {
    "homeassistant": types.ModuleType("homeassistant"),
    "homeassistant.const": _ha_const,
    "homeassistant.core": _ha_core,
    "homeassistant.config_entries": _ha_config_entries,
    "homeassistant.components": _ha_components,
    "homeassistant.components.sensor": _ha_sensor,
    "homeassistant.components.number": _ha_number,
    "homeassistant.components.button": _ha_button,
    "homeassistant.components.select": _ha_select,
    "homeassistant.helpers": _ha_helpers,
    "homeassistant.helpers.update_coordinator": _ha_update_coord,
    "homeassistant.helpers.device_registry": _ha_device_registry,
    "homeassistant.helpers.entity_platform": _ha_entity_platform,
    "homeassistant.helpers.service_info": _ha_helpers_service_info,
    "homeassistant.helpers.service_info.zeroconf": _ha_helpers_zeroconf,
    "homeassistant.helpers.selector": _ha_helpers_selector,
    "homeassistant.data_entry_flow": _ha_data_entry_flow,
}
sys.modules.update(_stubs)


# ───────────────────────────────────────────────────────────────────────
# 2b. Map the hyphenated package to a Python-importable name.
#
#     The custom component lives in ``custom_components/ducobox-connectivity-board/``
#     which cannot be imported with a regular ``import`` statement because of
#     the hyphens.  We add a sys.modules alias so that:
#
#         from custom_components.ducobox_connectivity_board.model.utils import safe_get
#
#     works transparently.
# ───────────────────────────────────────────────────────────────────────

import importlib
import pathlib

_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
_HYPHEN_PKG = _PROJECT_ROOT / "custom_components" / "ducobox-connectivity-board"

# Also mock ducopy (only coordinator.py imports it)
_ducopy = types.ModuleType("ducopy")
_ducopy.DucoPy = MagicMock
_ducopy_rest = types.ModuleType("ducopy.rest")
_ducopy_models = types.ModuleType("ducopy.rest.models")
_ducopy_models.ConfigNodeRequest = MagicMock
sys.modules["ducopy"] = _ducopy
sys.modules["ducopy.rest"] = _ducopy_rest
sys.modules["ducopy.rest.models"] = _ducopy_models

# Ensure custom_components is on sys.path for imports
_cc_path = str(_PROJECT_ROOT / "custom_components")
if _cc_path not in sys.path:
    sys.path.insert(0, _cc_path)

# Make sure custom_components package exists in sys.modules
if "custom_components" not in sys.modules:
    import custom_components  # noqa: F401

# Import the hyphenated package using importlib and register it under an
# underscore-based alias so normal Python imports work.
_real_pkg = importlib.import_module("ducobox-connectivity-board")
sys.modules["custom_components.ducobox_connectivity_board"] = _real_pkg

# Also register sub-modules so "from custom_components.ducobox_connectivity_board.model …" works
# Only register modules we actually need for testing (skip config_flow, number, select
# which pull in extra deps like voluptuous, requests, etc.)
for sub_name in ("const", "sensor", "button", "number", "select"):
    sub_mod = importlib.import_module(f"ducobox-connectivity-board.{sub_name}")
    sys.modules[f"custom_components.ducobox_connectivity_board.{sub_name}"] = sub_mod

# model package
_model_pkg = importlib.import_module("ducobox-connectivity-board.model")
sys.modules["custom_components.ducobox_connectivity_board.model"] = _model_pkg

for sub_name in ("utils", "devices", "coordinator"):
    sub_mod = importlib.import_module(f"ducobox-connectivity-board.model.{sub_name}")
    sys.modules[f"custom_components.ducobox_connectivity_board.model.{sub_name}"] = sub_mod


# ───────────────────────────────────────────────────────────────────────
# 3.  Realistic API response fixtures (captured from a live Ducobox)
# ───────────────────────────────────────────────────────────────────────

@pytest.fixture
def api_info_response() -> dict:
    """Full /info response from a Ducobox Energy Comfort (anonymized)."""
    return {
        'General': {
            'Board': {
                'ApiVersion': {'Val': '2.5.2.0'},
                'PublicApiVersion': {'Val': '2.5'},
                'SwVersionComm': {'Val': '21123.6.2.0'},
                'SwVersionBox': {'Val': '19156.7.7.0'},
                'BoxName': {'Val': 'ENERGY'},
                'BoxSubType': {'Val': 50},
                'BoxSubTypeName': {'Val': 'COMFORT_325_R'},
                'CommSubTypeName': {'Val': 'CONNECTIVITY'},
                'SerialBoardBox': {'Val': 'RS0000000001'},
                'SerialDucoBox': {'Val': 'P000000-000000-001'},
                'UpTime': {'Val': 10936},
                'Time': {'Val': 1700000000},
            },
            'Lan': {
                'Mode': {'Val': 'WIFI_CLIENT'},
                'Ip': {'Val': '192.168.0.100'},
                'Mac': {'Val': 'aa:bb:cc:dd:ee:ff'},
                'RssiWifi': {'Val': -56},
            },
            'NetworkDuco': {
                'HomeId': {'Val': '0x00FACADE'},
                'State': {'Val': 'OPERATIONAL'},
            },
            'PublicApi': {'WriteReqCntRemain': {'Val': 200}},
        },
        'Diag': {
            'Errors': [],
            'SubSystems': [{'Component': 'Ventilation', 'Status': 'Ok'}],
        },
        'Ventilation': {
            'Sensor': {
                'TempOda': {'Val': 108},
                'TempSup': {'Val': 198},
                'TempEta': {'Val': 195},
                'TempEha': {'Val': 158},
            },
            'Fan': {
                'SpeedSup': {'Val': 688},
                'PressSupTgt': {'Val': 8},
                'PressSup': {'Val': 89},
                'PwmSup': {'Val': 18},
                'PwmLvlSup': {'Val': 8000},
                'SpeedEha': {'Val': 857},
                'PressEha': {'Val': 167},
                'PressEhaTgt': {'Val': 16},
                'PwmEha': {'Val': 25},
                'PwmLvlEha': {'Val': 10192},
            },
            'Calibration': {
                'Valid': {'Val': True},
                'State': {'Val': 'IDLE'},
                'Status': {'Val': 'NOT_APPLICABLE'},
                'Error': {'Val': 0},
            },
        },
        'HeatRecovery': {
            'General': {'TimeFilterRemain': {'Val': 145}},
            'Bypass': {'Pos': {'Val': 0}, 'TempSupTgt': {'Val': 238}},
            'ProtectFrost': {'State': {'Val': 0}, 'PressReduct': {'Val': 0}, 'HeaterOdaPresent': {'Val': False}},
        },
        'NightBoost': {
            'General': {
                'TempOutsideAvgThs': {'Val': 120},
                'TempOutsideAvg': {'Val': 82},
                'TempOutside': {'Val': 96},
                'TempComfort': {'Val': 203},
                'TempZone1': {'Val': 186},
                'FlowLvlReqZone1': {'Val': 0},
            },
        },
        'VentCool': {
            'General': {
                'State': {'Val': 0},
                'TempOutsideAvgThs': {'Val': 120},
                'TempOutsideAvg': {'Val': 82},
                'TempInside': {'Val': 191},
                'TempInsideMin': {'Val': 204},
                'TempInsideMax': {'Val': 244},
                'TempComfort': {'Val': 220},
                'TempOutside': {'Val': 96},
            },
        },
    }


@pytest.fixture
def api_nodes_response() -> list[dict]:
    """Full /info/nodes → Nodes list (anonymized)."""
    return [
        {
            'Node': 1,
            'General': {
                'Type': {'Val': 'BOX'},
                'SubType': {'Val': 50},
                'NetworkType': {'Val': 'VIRT'},
                'Addr': {'Val': 1},
                'SwVersion': {'Val': '19156.7.7.0'},
                'SerialDuco': {'Val': 'P000000-000000-001'},
                'Name': {'Val': ''},
                'UpTime': {'Val': 10936},
            },
            'NetworkDuco': {'CommErrorCtr': {'Val': 0}},
            'Ventilation': {
                'State': {'Val': 'AUTO'},
                'TimeStateRemain': {'Val': 0},
                'TimeStateEnd': {'Val': 0},
                'Mode': {'Val': 'AUTO'},
                'FlowLvlTgt': {'Val': 30},
                'Pos': {'Val': 0},
                'FlowLvlOvrl': {'Val': 255},
                'FlowLvlReqSensor': {'Val': 0},
            },
            'Sensor': {
                'Temp': {'Val': 19.7},
                'Rh': {'Val': 51.34},
                'IaqRh': {'Val': 96},
            },
            'Diag': {'Errors': []},
        },
        {
            'Node': 2,
            'General': {
                'Type': {'Val': 'UCBAT'},
                'SubType': {'Val': 0},
                'NetworkType': {'Val': 'RF'},
                'Addr': {'Val': 2},
                'SwVersion': {'Val': 'n/a'},
                'SerialDuco': {'Val': 'n/a'},
                'Name': {'Val': ''},
            },
            'NetworkDuco': {
                'CommErrorCtr': {'Val': 0},
                'RssiRfN2M': {'Val': 0},
                'HopRf': {'Val': 2},
                'RssiRfN2H': {'Val': 0},
            },
            'Ventilation': {
                'State': {'Val': 'AUTO'},
                'TimeStateRemain': {'Val': 0},
                'TimeStateEnd': {'Val': 0},
                'Mode': {'Val': '-'},
                'FlowLvlOvrl': {'Val': 255},
                'FlowLvlReqSensor': {'Val': 0},
            },
            'Diag': {'Errors': []},
        },
        {
            'Node': 3,
            'General': {
                'Type': {'Val': 'UCCO2'},
                'SubType': {'Val': 1},
                'NetworkType': {'Val': 'RF'},
                'Addr': {'Val': 3},
                'SwVersion': {'Val': '17046.14.2.0'},
                'SerialDuco': {'Val': 'P000000-000000-002'},
                'Name': {'Val': ''},
                'UpTime': {'Val': 572},
            },
            'NetworkDuco': {
                'CommErrorCtr': {'Val': 0},
                'RssiRfN2M': {'Val': 125},
                'HopRf': {'Val': 3},
                'RssiRfN2H': {'Val': 255},
            },
            'Ventilation': {
                'State': {'Val': 'AUTO'},
                'TimeStateRemain': {'Val': 0},
                'TimeStateEnd': {'Val': 0},
                'Mode': {'Val': '-'},
                'FlowLvlOvrl': {'Val': 255},
                'FlowLvlReqSensor': {'Val': 0},
            },
            'Sensor': {
                'Temp': {'Val': 18.8},
                'Co2': {'Val': 1056},
                'IaqCo2': {'Val': 85},
            },
            'Diag': {'Errors': []},
        },
        {
            'Node': 52,
            'General': {
                'Type': {'Val': 'SWITCH'},
                'SubType': {'Val': 0},
                'NetworkType': {'Val': 'VIRT'},
                'Addr': {'Val': 1},
                'SwVersion': {'Val': 'n/a'},
                'SerialDuco': {'Val': 'n/a'},
                'Name': {'Val': ''},
            },
            'NetworkDuco': {'CommErrorCtr': {'Val': 0}},
            'Ventilation': {
                'State': {'Val': 'AUTO'},
                'TimeStateRemain': {'Val': 0},
                'TimeStateEnd': {'Val': 0},
                'Mode': {'Val': '-'},
                'FlowLvlOvrl': {'Val': 255},
                'FlowLvlReqSensor': {'Val': 0},
            },
            'Diag': {'Errors': []},
        },
        {
            'Node': 58,
            'General': {
                'Type': {'Val': 'BSRH'},
                'SubType': {'Val': 0},
                'NetworkType': {'Val': 'VIRT'},
                'Addr': {'Val': 1},
                'SwVersion': {'Val': 'n/a'},
                'SerialDuco': {'Val': 'n/a'},
                'Name': {'Val': ''},
            },
            'NetworkDuco': {'CommErrorCtr': {'Val': 0}},
            'Ventilation': {
                'State': {'Val': 'AUTO'},
                'TimeStateRemain': {'Val': 0},
                'TimeStateEnd': {'Val': 0},
                'Mode': {'Val': '-'},
                'FlowLvlOvrl': {'Val': 255},
                'FlowLvlReqSensor': {'Val': 10},
            },
            'Sensor': {
                'Temp': {'Val': 19.7},
                'Rh': {'Val': 51.34},
                'IaqRh': {'Val': 96},
            },
            'Diag': {'Errors': []},
        },
    ]


@pytest.fixture
def api_config_nodes_response() -> dict:
    """/config/nodes response (anonymized)."""
    return {
        'Nodes': [
            {
                'Node': 1,
                'SerialBoard': 'RS0000000001',
                'FlowLvlAutoMin': {'Val': 30, 'Min': 10, 'Inc': 5, 'Max': 80},
                'FlowLvlAutoMax': {'Val': 80, 'Min': 30, 'Inc': 5, 'Max': 100},
                'Name': {'Val': ''},
            },
            {
                'Node': 3,
                'SerialBoard': 'RS0000000002',
                'Co2SetPoint': {'Val': 1400, 'Min': 0, 'Inc': 10, 'Max': 2000},
                'Name': {'Val': ''},
            },
        ]
    }


@pytest.fixture
def api_config_response() -> dict:
    """Full /config response (anonymized)."""
    return {
        'General': {
            'Time': {'TimeZone': {'Val': 1, 'Min': -11, 'Inc': 1, 'Max': 12}},
            'Setup': {
                'Complete': {'Val': 1, 'Min': 1, 'Inc': 1, 'Max': 1},
                'Country': {'Val': 1, 'Min': 1, 'Inc': 1, 'Max': 1},
            },
            'Modbus': {'Addr': {'Val': 1, 'Min': 1, 'Inc': 1, 'Max': 254}},
            'Lan': {
                'TimeDucoClientIp': {'Val': 600, 'Min': 0, 'Inc': 1, 'Max': 3600},
                'Mode': {'Val': 1, 'Min': 0, 'Inc': 1, 'Max': 4},
                'Dhcp': {'Val': 1, 'Min': 0, 'Inc': 1, 'Max': 1},
            },
            'NodeData': {'UpdateRate': {'Val': 60, 'Min': 5, 'Inc': 1, 'Max': 3600}},
            'AutoRebootComm': {'Period': {'Val': 7, 'Min': 0, 'Inc': 1, 'Max': 365}},
            'PublicApi': {'DailyWriteReqCnt': {'Val': 0, 'Min': 0, 'Inc': 1, 'Max': 10000}},
        },
        'Ventilation': {
            'Ctrl': {
                'TempDepThsLow': {'Val': 160, 'Min': 100, 'Inc': 1, 'Max': 240},
                'TempDepThsHigh': {'Val': 240, 'Min': 160, 'Inc': 1, 'Max': 350},
            },
            'Calibration': {
                'PressSupCfgZone1': {'Val': 85, 'Min': 0, 'Inc': 1, 'Max': 999},
            },
        },
        'HeatRecovery': {
            'Bypass': {
                'TempSupTgtZone1': {'Val': 210, 'Min': 100, 'Inc': 1, 'Max': 255},
                'TimeFilter': {'Val': 180, 'Min': 90, 'Inc': 90, 'Max': 360},
            },
        },
        'NightBoost': {
            'General': {
                'TempStart': {'Val': 24, 'Min': 0, 'Inc': 1, 'Max': 60},
                'FlowLvlReqMax': {'Val': 100, 'Min': 10, 'Inc': 5, 'Max': 100},
            },
        },
        'VentCool': {
            'General': {
                'TimeStart': {'Val': 1320, 'Min': 0, 'Inc': 1, 'Max': 1439},
                'SpeedWindMax': {'Val': 110, 'Min': 0, 'Inc': 1, 'Max': 200},
            },
        },
        'Firmware': {
            'General': {'DowngradeAllow': {'Val': 0, 'Min': 0, 'Inc': 1, 'Max': 1}},
        },
        'Azure': {
            'Connection': {'Enable': {'Val': 1, 'Min': 0, 'Inc': 1, 'Max': 1}},
        },
    }


@pytest.fixture
def api_action_response() -> dict:
    """Full /action response (anonymized)."""
    return {
        'Actions': [
            {'Action': 'ResetFilterTimeRemain', 'ValType': 'None'},
            {'Action': 'UpdateNodeData', 'ValType': 'None'},
            {'Action': 'ReconnectWifi', 'ValType': 'None'},
            {'Action': 'ScanWifi', 'ValType': 'None'},
            {'Action': 'RebootBox', 'ValType': 'None'},
        ]
    }


@pytest.fixture
def api_action_nodes_response() -> dict:
    """Full /action/nodes response (anonymized)."""
    return {
        'Nodes': [
            {
                'Node': 1,
                'Actions': [
                    {
                        'Action': 'SetVentilationState',
                        'Enum': ['AUTO', 'MAN1', 'MAN2', 'MAN3'],
                    },
                ],
            },
            {
                'Node': 3,
                'Actions': [
                    {
                        'Action': 'SetVentilationState',
                        'Enum': ['AUTO', 'MAN1', 'MAN2', 'MAN3'],
                    },
                ],
            },
        ]
    }


@pytest.fixture
def coordinator_data(api_info_response, api_nodes_response, api_config_nodes_response,
                     api_config_response, api_action_response, api_action_nodes_response) -> dict:
    """Combined data dict as the coordinator would produce."""
    data = {
        'info': api_info_response,
        'nodes': api_nodes_response,
        'config_nodes': api_config_nodes_response,
        'config': api_config_response,
        'action': api_action_response,
        'mappings': {
            'node_id_to_name': {},
            'node_id_to_type': {},
        },
        'action_nodes': api_action_nodes_response,
    }
    for node in api_nodes_response:
        nid = node['Node']
        ntype = node.get('General', {}).get('Type', {}).get('Val', 'Unknown')
        data['mappings']['node_id_to_name'][nid] = f"{nid}:{ntype}"
        data['mappings']['node_id_to_type'][nid] = ntype
    return data
