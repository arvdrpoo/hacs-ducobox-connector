"""Tests for sensor definitions and auto-discovery (devices.py).

Covers:
- _humanize_key()
- _make_value_fn_processed / _make_value_fn_raw
- discover_node_sensors() with known & unknown keys
- NODE_SENSOR_REGISTRY completeness
- Box-level SENSORS value_fn calls against realistic /info data
"""

import pytest
from custom_components.ducobox_connectivity_board.model.devices import (
    DucoboxSensorEntityDescription,
    DucoboxNodeSensorEntityDescription,
    NodeSensorMeta,
    NODE_SENSOR_REGISTRY,
    SENSORS,
    discover_node_sensors,
    _humanize_key,
    _make_value_fn_processed,
    _make_value_fn_raw,
)


# ── _humanize_key ─────────────────────────────────────────────────────

class TestHumanizeKey:

    def test_camel_case(self):
        assert _humanize_key("FlowLvlTgt") == "Flow Lvl Tgt"

    def test_simple(self):
        assert _humanize_key("Temp") == "Temp"

    def test_consecutive_uppercase(self):
        # "IaqRh" should become "Iaq Rh"
        assert _humanize_key("IaqRh") == "Iaq Rh"

    def test_all_uppercase(self):
        # "RF" stays as "RF"
        assert _humanize_key("RF") == "RF"

    def test_single_char(self):
        assert _humanize_key("A") == "A"

    def test_acronym_before_word(self):
        assert _humanize_key("RSSIWifi") == "RSSI Wifi"

    def test_lowercase_only(self):
        assert _humanize_key("temperature") == "temperature"


# ── _make_value_fn_processed ──────────────────────────────────────────

class TestMakeValueFnProcessed:

    def test_extracts_and_processes(self):
        fn = _make_value_fn_processed('Sensor', 'Temp', lambda v: v * 2)
        node = {'Sensor': {'Temp': {'Val': 10}}}
        assert fn(node) == 20

    def test_missing_module_returns_none(self):
        fn = _make_value_fn_processed('Sensor', 'Temp', lambda v: v * 2 if v is not None else None)
        node = {'Ventilation': {}}
        # process_fn receives None (extract_val(None) → None)
        assert fn(node) is None

    def test_missing_key_returns_none(self):
        fn = _make_value_fn_processed('Sensor', 'Temp', lambda v: v * 2 if v is not None else None)
        node = {'Sensor': {'Rh': {'Val': 50}}}
        assert fn(node) is None

    def test_process_fn_with_none(self):
        """process_fn receives None when data is absent."""
        fn = _make_value_fn_processed('Sensor', 'Co2', lambda v: v)
        node = {}
        assert fn(node) is None


# ── _make_value_fn_raw ────────────────────────────────────────────────

class TestMakeValueFnRaw:

    def test_extracts_val(self):
        fn = _make_value_fn_raw('Sensor', 'Temp')
        node = {'Sensor': {'Temp': {'Val': 19.7}}}
        assert fn(node) == 19.7

    def test_missing_returns_none(self):
        fn = _make_value_fn_raw('Sensor', 'Temp')
        assert fn({}) is None

    def test_string_val(self):
        fn = _make_value_fn_raw('Ventilation', 'State')
        node = {'Ventilation': {'State': {'Val': 'AUTO'}}}
        assert fn(node) == 'AUTO'


# ── NODE_SENSOR_REGISTRY ─────────────────────────────────────────────

class TestNodeSensorRegistry:

    def test_known_modules(self):
        assert 'Sensor' in NODE_SENSOR_REGISTRY
        assert 'Ventilation' in NODE_SENSOR_REGISTRY
        assert 'NetworkDuco' in NODE_SENSOR_REGISTRY
        assert 'General' in NODE_SENSOR_REGISTRY

    def test_sensor_keys(self):
        sensor_keys = set(NODE_SENSOR_REGISTRY['Sensor'].keys())
        assert sensor_keys == {'Temp', 'Rh', 'IaqRh', 'Co2', 'IaqCo2'}

    def test_ventilation_keys(self):
        vent_keys = set(NODE_SENSOR_REGISTRY['Ventilation'].keys())
        expected = {
            'State', 'Mode', 'FlowLvlTgt', 'TimeStateRemain',
            'TimeStateEnd', 'Pos', 'FlowLvlOvrl', 'FlowLvlReqSensor',
        }
        assert vent_keys == expected

    def test_network_keys(self):
        net_keys = set(NODE_SENSOR_REGISTRY['NetworkDuco'].keys())
        assert net_keys == {'CommErrorCtr', 'RssiRfN2M', 'RssiRfN2H', 'HopRf'}

    def test_all_entries_are_node_sensor_meta(self):
        for module, keys in NODE_SENSOR_REGISTRY.items():
            for key, meta in keys.items():
                assert isinstance(meta, NodeSensorMeta), f"{module}.{key} is not NodeSensorMeta"

    def test_temp_has_correct_device_class(self):
        meta = NODE_SENSOR_REGISTRY['Sensor']['Temp']
        assert meta.device_class is not None
        assert meta.device_class.value == 'temperature'

    def test_rh_has_correct_device_class(self):
        meta = NODE_SENSOR_REGISTRY['Sensor']['Rh']
        assert meta.device_class is not None
        assert meta.device_class.value == 'humidity'

    def test_co2_has_correct_device_class(self):
        meta = NODE_SENSOR_REGISTRY['Sensor']['Co2']
        assert meta.device_class is not None
        assert meta.device_class.value == 'carbon_dioxide'


# ── discover_node_sensors ────────────────────────────────────────────

class TestDiscoverNodeSensors:

    def test_box_node(self, api_nodes_response):
        """BOX node (id=1) has Sensor, Ventilation, and NetworkDuco modules."""
        node = api_nodes_response[0]
        assert node['General']['Type']['Val'] == 'BOX'

        descriptions = discover_node_sensors(node)

        # Collect all sensor keys
        keys = {d.sensor_key for d in descriptions}

        # Sensor module
        assert 'Sensor_Temp' in keys
        assert 'Sensor_Rh' in keys
        assert 'Sensor_IaqRh' in keys

        # Ventilation module
        assert 'Ventilation_State' in keys
        assert 'Ventilation_Mode' in keys
        assert 'Ventilation_FlowLvlTgt' in keys

        # NetworkDuco module
        assert 'NetworkDuco_CommErrorCtr' in keys

    def test_ucco2_node(self, api_nodes_response):
        """UCCO2 node (id=3) has CO₂ sensor."""
        node = api_nodes_response[2]
        assert node['General']['Type']['Val'] == 'UCCO2'

        descriptions = discover_node_sensors(node)
        keys = {d.sensor_key for d in descriptions}

        assert 'Sensor_Co2' in keys
        assert 'Sensor_IaqCo2' in keys
        assert 'Sensor_Temp' in keys

    def test_bsrh_node(self, api_nodes_response):
        """BSRH node (id=58) has Rh and IaqRh sensors — the original bug."""
        node = api_nodes_response[4]
        assert node['General']['Type']['Val'] == 'BSRH'

        descriptions = discover_node_sensors(node)
        keys = {d.sensor_key for d in descriptions}

        assert 'Sensor_Temp' in keys
        assert 'Sensor_Rh' in keys
        assert 'Sensor_IaqRh' in keys

    def test_ucbat_node_has_no_sensor_module(self, api_nodes_response):
        """UCBAT node (id=2) has no Sensor module, only Ventilation and NetworkDuco."""
        node = api_nodes_response[1]
        assert node['General']['Type']['Val'] == 'UCBAT'

        descriptions = discover_node_sensors(node)
        keys = {d.sensor_key for d in descriptions}

        # No Sensor module → no Sensor_* keys
        assert not any(k.startswith('Sensor_') for k in keys)

        # But Ventilation and NetworkDuco keys should exist
        assert 'Ventilation_State' in keys
        assert 'NetworkDuco_CommErrorCtr' in keys

    def test_switch_node_minimal(self, api_nodes_response):
        """SWITCH node (id=52) has only Ventilation and NetworkDuco."""
        node = api_nodes_response[3]
        assert node['General']['Type']['Val'] == 'SWITCH'

        descriptions = discover_node_sensors(node)
        keys = {d.sensor_key for d in descriptions}

        assert not any(k.startswith('Sensor_') for k in keys)
        assert 'Ventilation_State' in keys

    def test_known_sensor_has_metadata(self, api_nodes_response):
        """Known sensor keys get rich metadata from the registry."""
        node = api_nodes_response[0]  # BOX
        descriptions = discover_node_sensors(node)

        temp_desc = next(d for d in descriptions if d.sensor_key == 'Sensor_Temp')
        assert temp_desc.name == 'Temperature'
        assert temp_desc.device_class is not None
        assert temp_desc.native_unit_of_measurement == '°C'

    def test_value_fn_works_for_known_sensor(self, api_nodes_response):
        """value_fn correctly extracts values from real node data."""
        node = api_nodes_response[0]  # BOX: Sensor.Temp.Val = 19.7
        descriptions = discover_node_sensors(node)

        temp_desc = next(d for d in descriptions if d.sensor_key == 'Sensor_Temp')
        assert temp_desc.value_fn(node) == pytest.approx(19.7)

    def test_value_fn_works_for_co2(self, api_nodes_response):
        node = api_nodes_response[2]  # UCCO2: Sensor.Co2.Val = 1056
        descriptions = discover_node_sensors(node)

        co2_desc = next(d for d in descriptions if d.sensor_key == 'Sensor_Co2')
        assert co2_desc.value_fn(node) == 1056

    def test_value_fn_works_for_ventilation_state(self, api_nodes_response):
        node = api_nodes_response[0]
        descriptions = discover_node_sensors(node)

        state_desc = next(d for d in descriptions if d.sensor_key == 'Ventilation_State')
        assert state_desc.value_fn(node) == 'AUTO'

    def test_auto_discovers_unknown_key(self):
        """Unknown keys in a known module get auto-discovered."""
        node = {
            'Node': 99,
            'General': {'Type': {'Val': 'FUTURE_TYPE'}},
            'Sensor': {
                'Temp': {'Val': 20.0},        # known
                'NewSensor': {'Val': 123},     # unknown
            },
        }
        descriptions = discover_node_sensors(node)
        keys = {d.sensor_key for d in descriptions}

        assert 'Sensor_Temp' in keys
        assert 'Sensor_NewSensor' in keys

        # The unknown key should have a humanized name
        new_desc = next(d for d in descriptions if d.sensor_key == 'Sensor_NewSensor')
        assert 'New Sensor' in new_desc.name
        assert new_desc.value_fn(node) == 123

    def test_auto_discovers_unknown_module_key(self):
        """Keys in a scanned module that aren't in the registry still work."""
        node = {
            'Node': 99,
            'General': {'Type': {'Val': 'MAGIC'}},
            'Ventilation': {
                'State': {'Val': 'MANUAL'},    # known
                'SpeedExtra': {'Val': 42},     # unknown
            },
        }
        descriptions = discover_node_sensors(node)
        keys = {d.sensor_key for d in descriptions}

        assert 'Ventilation_SpeedExtra' in keys

    def test_skips_non_val_keys(self):
        """Entries without {'Val': ...} structure are ignored."""
        node = {
            'Node': 99,
            'General': {'Type': {'Val': 'TEST'}},
            'Sensor': {
                'Temp': {'Val': 20.0},
                'Errors': [],               # Not a Val dict
                'Other': 'raw_string',       # Not a Val dict
            },
        }
        descriptions = discover_node_sensors(node)
        keys = {d.sensor_key for d in descriptions}

        assert 'Sensor_Temp' in keys
        assert 'Sensor_Errors' not in keys
        assert 'Sensor_Other' not in keys

    def test_skips_unscanned_modules(self):
        """Modules not in the scan list (e.g. 'Diag') are ignored."""
        node = {
            'Node': 1,
            'General': {'Type': {'Val': 'BOX'}},
            'Diag': {'Errors': []},
        }
        descriptions = discover_node_sensors(node)
        # General module is scanned but Type is in the skip list, so no sensors
        assert len(descriptions) == 0

    def test_returns_list_of_correct_type(self, api_nodes_response):
        node = api_nodes_response[0]
        descriptions = discover_node_sensors(node)
        assert isinstance(descriptions, list)
        for d in descriptions:
            assert isinstance(d, DucoboxNodeSensorEntityDescription)

    def test_descriptions_are_frozen(self, api_nodes_response):
        """Descriptions are frozen dataclasses — immutable."""
        node = api_nodes_response[0]
        descriptions = discover_node_sensors(node)
        desc = descriptions[0]
        with pytest.raises(AttributeError):
            desc.name = "tampered"

    def test_data_path_set_correctly(self, api_nodes_response):
        node = api_nodes_response[0]
        descriptions = discover_node_sensors(node)

        temp = next(d for d in descriptions if d.sensor_key == 'Sensor_Temp')
        assert temp.data_path == ('Sensor', 'Temp')

        state = next(d for d in descriptions if d.sensor_key == 'Ventilation_State')
        assert state.data_path == ('Ventilation', 'State')


# ── Box-level SENSORS value_fn ────────────────────────────────────────

class TestBoxSensorsValueFn:
    """Test that each box-level SENSORS entry extracts the correct value
    from a realistic /info response."""

    def test_sensor_count(self):
        """Sanity check: we have a reasonable number of box-level sensors."""
        assert len(SENSORS) >= 30

    def test_all_have_value_fn(self):
        for s in SENSORS:
            assert callable(s.value_fn), f"Sensor {s.key} has no value_fn"

    def test_all_have_data_path(self):
        for s in SENSORS:
            assert s.data_path is not None, f"Sensor {s.key} has no data_path"

    def test_temp_oda(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'TempOda')
        assert s.value_fn(coordinator_data) == pytest.approx(10.8)

    def test_temp_sup(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'TempSup')
        assert s.value_fn(coordinator_data) == pytest.approx(19.8)

    def test_temp_eta(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'TempEta')
        assert s.value_fn(coordinator_data) == pytest.approx(19.5)

    def test_temp_eha(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'TempEha')
        assert s.value_fn(coordinator_data) == pytest.approx(15.8)

    def test_speed_sup(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'SpeedSup')
        assert s.value_fn(coordinator_data) == 688

    def test_speed_eha(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'SpeedEha')
        assert s.value_fn(coordinator_data) == 857

    def test_press_sup(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'PressSup')
        assert s.value_fn(coordinator_data) == pytest.approx(8.9)

    def test_press_eha(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'PressEha')
        assert s.value_fn(coordinator_data) == pytest.approx(16.7)

    def test_pwm_sup(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'PwmSup')
        assert s.value_fn(coordinator_data) == 18

    def test_pwm_eha(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'PwmEha')
        assert s.value_fn(coordinator_data) == 25

    def test_press_sup_tgt(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'PressSupTgt')
        assert s.value_fn(coordinator_data) == pytest.approx(0.8)

    def test_press_eha_tgt(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'PressEhaTgt')
        assert s.value_fn(coordinator_data) == pytest.approx(1.6)

    def test_rssi_wifi(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'RssiWifi')
        assert s.value_fn(coordinator_data) == -56

    def test_uptime(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'UpTime')
        assert s.value_fn(coordinator_data) == 10936

    def test_time_filter_remain(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'TimeFilterRemain')
        assert s.value_fn(coordinator_data) == 145

    def test_bypass_pos(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'BypassPos')
        assert s.value_fn(coordinator_data) == 0

    def test_bypass_temp_sup_tgt(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'BypassTempSupTgt')
        assert s.value_fn(coordinator_data) == pytest.approx(23.8)

    def test_frost_protect_state(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'FrostProtectState')
        assert s.value_fn(coordinator_data) == 0

    def test_night_boost_temp_outside(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'NightBoostTempOutsideAvg')
        assert s.value_fn(coordinator_data) == pytest.approx(8.2)

    def test_ventcool_state(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'VentCoolState')
        assert s.value_fn(coordinator_data) == 0

    def test_ventcool_temp_inside(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'VentCoolTempInside')
        assert s.value_fn(coordinator_data) == pytest.approx(19.1)

    def test_diag_status(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'DiagStatus')
        assert s.value_fn(coordinator_data) == 'Ok'

    def test_sensor_returns_none_when_data_missing(self):
        """value_fn should return None when the data path doesn't exist."""
        empty_data = {'info': {}}
        for s in SENSORS:
            result = s.value_fn(empty_data)
            assert result is None, f"Sensor {s.key} returned {result} for empty data"

    # -- New sensors added in expansion --

    def test_nightboost_temp_outside_avg_ths(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'NightBoostTempOutsideAvgThs')
        assert s.value_fn(coordinator_data) == pytest.approx(12.0)

    def test_nightboost_temp_outside(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'NightBoostTempOutside')
        assert s.value_fn(coordinator_data) == pytest.approx(9.6)

    def test_nightboost_temp_comfort(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'NightBoostTempComfort')
        assert s.value_fn(coordinator_data) == pytest.approx(20.3)

    def test_nightboost_temp_zone1(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'NightBoostTempZone1')
        assert s.value_fn(coordinator_data) == pytest.approx(18.6)

    def test_ventcool_temp_outside_avg_ths(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'VentCoolTempOutsideAvgThs')
        assert s.value_fn(coordinator_data) == pytest.approx(12.0)

    def test_ventcool_temp_outside_avg(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'VentCoolTempOutsideAvg')
        assert s.value_fn(coordinator_data) == pytest.approx(8.2)

    def test_ventcool_temp_inside_min(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'VentCoolTempInsideMin')
        assert s.value_fn(coordinator_data) == pytest.approx(20.4)

    def test_ventcool_temp_inside_max(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'VentCoolTempInsideMax')
        assert s.value_fn(coordinator_data) == pytest.approx(24.4)

    def test_ventcool_temp_comfort(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'VentCoolTempComfort')
        assert s.value_fn(coordinator_data) == pytest.approx(22.0)

    def test_ventcool_temp_outside(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'VentCoolTempOutside')
        assert s.value_fn(coordinator_data) == pytest.approx(9.6)

    def test_pwm_lvl_sup(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'PwmLvlSup')
        assert s.value_fn(coordinator_data) == 8000

    def test_pwm_lvl_eha(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'PwmLvlEha')
        assert s.value_fn(coordinator_data) == 10192

    def test_calibration_state(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'CalibrationState')
        assert s.value_fn(coordinator_data) == 'IDLE'

    def test_calibration_status(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'CalibrationStatus')
        assert s.value_fn(coordinator_data) == 'NOT_APPLICABLE'

    def test_lan_mode(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'LanMode')
        assert s.value_fn(coordinator_data) == 'WIFI_CLIENT'

    def test_lan_ip(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'LanIp')
        assert s.value_fn(coordinator_data) == '192.168.0.100'

    def test_network_duco_state(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'NetworkDucoState')
        assert s.value_fn(coordinator_data) == 'OPERATIONAL'

    def test_public_api_write_req(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'PublicApiWriteReqCntRemain')
        assert s.value_fn(coordinator_data) == 200

    def test_heater_oda_present(self, coordinator_data):
        s = next(s for s in SENSORS if s.key == 'HeaterOdaPresent')
        assert s.value_fn(coordinator_data) is False


# ── General module in node discovery ──────────────────────────────────

class TestGeneralModuleDiscovery:

    def test_discovers_uptime_from_general(self):
        node = {
            'Node': 1,
            'General': {
                'Type': {'Val': 'BOX'},
                'UpTime': {'Val': 10936},
                'Name': {'Val': 'Test'},
            },
        }
        descriptions = discover_node_sensors(node)
        keys = {d.sensor_key for d in descriptions}
        assert 'General_UpTime' in keys

    def test_skips_type_in_general(self):
        node = {
            'Node': 1,
            'General': {
                'Type': {'Val': 'BOX'},
            },
        }
        descriptions = discover_node_sensors(node)
        keys = {d.sensor_key for d in descriptions}
        assert 'General_Type' not in keys

    def test_skips_name_in_general(self):
        node = {
            'Node': 1,
            'General': {
                'Type': {'Val': 'BOX'},
                'Name': {'Val': 'test'},
            },
        }
        descriptions = discover_node_sensors(node)
        keys = {d.sensor_key for d in descriptions}
        assert 'General_Name' not in keys

    def test_uptime_has_duration_device_class(self):
        node = {
            'Node': 1,
            'General': {
                'Type': {'Val': 'BOX'},
                'UpTime': {'Val': 500},
            },
        }
        descriptions = discover_node_sensors(node)
        uptime = next(d for d in descriptions if d.sensor_key == 'General_UpTime')
        assert uptime.device_class is not None
        assert uptime.device_class.value == 'duration'
