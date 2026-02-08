"""Tests for custom_components.ducobox-connectivity-board.model.utils"""

from custom_components.ducobox_connectivity_board.model.utils import (
    safe_get,
    extract_val,
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
)

import pytest


# ── safe_get ──────────────────────────────────────────────────────────

class TestSafeGet:
    """Tests for safe_get(), the nested-dict traversal helper."""

    def test_single_level(self):
        assert safe_get({'a': 1}, 'a') == 1

    def test_nested(self):
        data = {'a': {'b': {'c': 42}}}
        assert safe_get(data, 'a', 'b', 'c') == 42

    def test_missing_key_returns_none(self):
        assert safe_get({'a': 1}, 'b') is None

    def test_missing_deep_key_returns_none(self):
        assert safe_get({'a': {'b': 1}}, 'a', 'x') is None

    def test_intermediate_not_dict_returns_none(self):
        assert safe_get({'a': 42}, 'a', 'b') is None

    def test_empty_keys_returns_data(self):
        data = {'hello': 'world'}
        assert safe_get(data) == data

    def test_none_data(self):
        assert safe_get(None, 'a') is None

    def test_list_not_traversable(self):
        """safe_get works on dicts, not lists."""
        assert safe_get([1, 2, 3], 0) is None

    def test_integer_key_on_dict(self):
        """Dicts can have integer keys; safe_get should handle them."""
        data = {0: 'zero', 1: 'one'}
        assert safe_get(data, 0) == 'zero'

    def test_val_pattern(self):
        """Typical API pattern: dict with 'Val' key."""
        data = {'Sensor': {'Temp': {'Val': 19.7}}}
        assert safe_get(data, 'Sensor', 'Temp', 'Val') == 19.7

    def test_returns_sub_dict(self):
        """Getting a key that is itself a dict returns that dict."""
        inner = {'Val': 5}
        data = {'Sensor': {'Temp': inner}}
        assert safe_get(data, 'Sensor', 'Temp') is inner


# ── extract_val ───────────────────────────────────────────────────────

class TestExtractVal:
    """Tests for extract_val(), which unwraps {'Val': x} dicts."""

    def test_unwraps_val_dict(self):
        assert extract_val({'Val': 42}) == 42

    def test_unwraps_val_float(self):
        assert extract_val({'Val': 19.7}) == 19.7

    def test_unwraps_val_string(self):
        assert extract_val({'Val': 'AUTO'}) == 'AUTO'

    def test_unwraps_val_zero(self):
        """Zero is a valid Val."""
        assert extract_val({'Val': 0}) == 0

    def test_unwraps_val_none(self):
        """None is a valid Val."""
        assert extract_val({'Val': None}) is None

    def test_passthrough_non_dict(self):
        assert extract_val(42) == 42
        assert extract_val('hello') == 'hello'

    def test_passthrough_dict_without_val(self):
        d = {'Other': 5}
        assert extract_val(d) == d

    def test_passthrough_none(self):
        assert extract_val(None) is None

    def test_dict_with_val_and_extras(self):
        """Even if the dict has more keys, Val is extracted."""
        assert extract_val({'Val': 10, 'Min': 0, 'Max': 100}) == 10


# ── process_temperature ──────────────────────────────────────────────

class TestProcessTemperature:
    """process_temperature divides raw value by 10."""

    def test_normal(self):
        assert process_temperature(108) == pytest.approx(10.8)

    def test_negative(self):
        assert process_temperature(-50) == pytest.approx(-5.0)

    def test_zero(self):
        assert process_temperature(0) == pytest.approx(0.0)

    def test_none(self):
        assert process_temperature(None) is None


# ── process_pressure ─────────────────────────────────────────────────

class TestProcessPressure:
    """process_pressure multiplies by 0.1."""

    def test_normal(self):
        assert process_pressure(89) == pytest.approx(8.9)

    def test_zero(self):
        assert process_pressure(0) == pytest.approx(0.0)

    def test_none(self):
        assert process_pressure(None) is None

    def test_string_number(self):
        """API could return a string; float conversion should handle it."""
        assert process_pressure("167") == pytest.approx(16.7)


# ── process_bypass_position ──────────────────────────────────────────

class TestProcessBypassPosition:
    """process_bypass_position rounds to int."""

    def test_already_integer(self):
        assert process_bypass_position(50) == 50

    def test_float_rounds(self):
        assert process_bypass_position(49.6) == 50

    def test_float_rounds_down(self):
        assert process_bypass_position(49.4) == 49

    def test_zero(self):
        assert process_bypass_position(0) == 0

    def test_none(self):
        assert process_bypass_position(None) is None

    def test_string_number(self):
        assert process_bypass_position("50.7") == 51


# ── Pass-through node processing functions ───────────────────────────

class TestPassthroughProcessors:
    """Node processing functions pass values through unchanged."""

    @pytest.mark.parametrize(
        "fn",
        [
            process_node_temperature,
            process_node_humidity,
            process_node_co2,
            process_node_iaq,
            process_speed,
            process_rssi,
            process_uptime,
            process_timefilterremain,
        ],
    )
    def test_passthrough_value(self, fn):
        assert fn(42) == 42

    @pytest.mark.parametrize(
        "fn",
        [
            process_node_temperature,
            process_node_humidity,
            process_node_co2,
            process_node_iaq,
            process_speed,
            process_rssi,
            process_uptime,
            process_timefilterremain,
        ],
    )
    def test_passthrough_none(self, fn):
        assert fn(None) is None

    @pytest.mark.parametrize(
        "fn",
        [
            process_node_temperature,
            process_node_humidity,
            process_node_co2,
            process_node_iaq,
            process_speed,
            process_rssi,
            process_uptime,
            process_timefilterremain,
        ],
    )
    def test_passthrough_float(self, fn):
        assert fn(19.7) == 19.7
