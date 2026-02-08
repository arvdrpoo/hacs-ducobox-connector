"""Tests for number.py — number platform entities."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from custom_components.ducobox_connectivity_board.number import (
    async_setup_entry,
    DucoboxNodeNumberEntity,
    DucoboxBoxNumberEntity,
    _is_number_param,
    _humanize_config_key,
)
from custom_components.ducobox_connectivity_board.const import DOMAIN


@pytest.fixture
def mock_coordinator(coordinator_data):
    coord = MagicMock()
    coord.data = coordinator_data
    coord.last_update_success = True
    coord.async_set_value = AsyncMock()
    coord.async_set_box_config = AsyncMock()
    coord.async_request_refresh = AsyncMock()
    return coord


@pytest.fixture
def mock_hass(mock_coordinator):
    hass = MagicMock()
    entry_id = 'test_entry_123'
    hass.data = {DOMAIN: {entry_id: {'coordinator': mock_coordinator}}}
    return hass, entry_id


@pytest.fixture
def mock_entry(mock_hass):
    hass, entry_id = mock_hass
    entry = MagicMock()
    entry.entry_id = entry_id
    return entry


class TestIsNumberParam:

    def test_valid(self):
        assert _is_number_param({'Val': 10, 'Min': 0, 'Max': 100, 'Inc': 1}) is True

    def test_missing_val(self):
        assert _is_number_param({'Min': 0, 'Max': 100, 'Inc': 1}) is False

    def test_missing_min(self):
        assert _is_number_param({'Val': 10, 'Max': 100, 'Inc': 1}) is False

    def test_not_dict(self):
        assert _is_number_param('hello') is False

    def test_plain_val_dict(self):
        assert _is_number_param({'Val': 'test'}) is False


class TestHumanizeConfigKey:

    def test_camel_case(self):
        assert _humanize_config_key('FlowMax') == 'Flow Max'

    def test_acronym(self):
        assert _humanize_config_key('TimeFilter') == 'Time Filter'


class TestNumberSetupEntry:

    @pytest.mark.asyncio
    async def test_creates_node_number_entities(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        node_entities = [e for e in added_entities if isinstance(e, DucoboxNodeNumberEntity)]
        assert len(node_entities) > 0

    @pytest.mark.asyncio
    async def test_creates_box_number_entities(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        box_entities = [e for e in added_entities if isinstance(e, DucoboxBoxNumberEntity)]
        assert len(box_entities) > 0

    @pytest.mark.asyncio
    async def test_unique_ids_unique(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        unique_ids = [e._attr_unique_id for e in added_entities]
        assert len(unique_ids) == len(set(unique_ids))

    @pytest.mark.asyncio
    async def test_skips_on_unknown_mac(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        mock_coordinator.data['info']['General']['Lan']['Mac'] = {'Val': None}
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        assert len(added_entities) == 0

    @pytest.mark.asyncio
    async def test_skips_excluded_submodules(self, mock_hass, mock_entry, mock_coordinator):
        """Entire submodules in the skip set should be excluded."""
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        box_ids = {e._attr_unique_id for e in added_entities if isinstance(e, DucoboxBoxNumberEntity)}
        # These submodules are fully excluded
        assert not any('General-Setup' in uid for uid in box_ids)
        assert not any('General-Modbus' in uid for uid in box_ids)
        assert not any('General-AutoRebootComm' in uid for uid in box_ids)
        assert not any('General-PublicApi' in uid for uid in box_ids)
        assert not any('Firmware-General' in uid for uid in box_ids)
        assert not any('Azure-Connection' in uid for uid in box_ids)

    @pytest.mark.asyncio
    async def test_skips_excluded_individual_keys(self, mock_hass, mock_entry, mock_coordinator):
        """Individual keys in the key-level skip set should be excluded."""
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        box_ids = {e._attr_unique_id for e in added_entities if isinstance(e, DucoboxBoxNumberEntity)}
        assert not any('TimeDucoClientIp' in uid for uid in box_ids)
        assert not any('General-Lan-Mode' in uid for uid in box_ids)
        assert not any('General-Lan-Dhcp' in uid for uid in box_ids)

    @pytest.mark.asyncio
    async def test_skips_fixed_min_equals_max(self, mock_hass, mock_entry, mock_coordinator):
        """Parameters where Min == Max are not user-configurable and should be excluded."""
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        box_ids = {e._attr_unique_id for e in added_entities if isinstance(e, DucoboxBoxNumberEntity)}
        # Setup.Complete has Min==Max==1, should be skipped even if submodule wasn't excluded
        assert not any('Complete' in uid for uid in box_ids)
        assert not any('Country' in uid for uid in box_ids)

    @pytest.mark.asyncio
    async def test_includes_useful_params(self, mock_hass, mock_entry, mock_coordinator):
        """Useful parameters should still be created."""
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        box_ids = {e._attr_unique_id for e in added_entities if isinstance(e, DucoboxBoxNumberEntity)}
        assert any('TimeFilter' in uid for uid in box_ids)
        assert any('TempStart' in uid for uid in box_ids)
        assert any('SpeedWindMax' in uid for uid in box_ids)
        assert any('TempSupTgtZone1' in uid for uid in box_ids)

    @pytest.mark.asyncio
    async def test_skips_boolean_params(self, mock_hass, mock_entry, mock_coordinator):
        """Boolean params (Min=0, Max=1) belong in switch platform, not number."""
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        box_ids = {e._attr_unique_id for e in added_entities if isinstance(e, DucoboxBoxNumberEntity)}
        assert not any('EnableMonday' in uid for uid in box_ids)
        assert not any('TempDepEnable' in uid for uid in box_ids)
        assert not any('Adaptive' in uid for uid in box_ids)
        assert not any('NightBoost' in uid and 'Enable' in uid for uid in box_ids)

    @pytest.mark.asyncio
    async def test_skips_enum_select_params(self, mock_hass, mock_entry, mock_coordinator):
        """Enum-like params in _CONFIG_SELECT_PARAMS belong in select platform."""
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        box_ids = {e._attr_unique_id for e in added_entities if isinstance(e, DucoboxBoxNumberEntity)}
        # Bypass.Mode and VentCool.General.Mode should be selects, not numbers
        assert not any('Bypass-Mode' in uid for uid in box_ids)
        assert not any('VentCool-General-Mode' in uid for uid in box_ids)


class TestTemperatureScaling:
    """Temperature parameters stored in tenths should display as °C."""

    @pytest.mark.asyncio
    async def test_temp_entity_has_celsius_unit(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        temp_entity = next(
            e for e in added_entities
            if isinstance(e, DucoboxBoxNumberEntity) and 'TempSupTgtZone1' in e._attr_unique_id
        )
        assert temp_entity._attr_native_unit_of_measurement == '°C'

    @pytest.mark.asyncio
    async def test_temp_entity_range_scaled(self, mock_hass, mock_entry, mock_coordinator):
        """Min/Max/Step should be divided by 10 for tenths-of-degree params."""
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        temp_entity = next(
            e for e in added_entities
            if isinstance(e, DucoboxBoxNumberEntity) and 'TempSupTgtZone1' in e._attr_unique_id
        )
        assert temp_entity._attr_native_min_value == 10.0
        assert temp_entity._attr_native_max_value == 25.5
        assert temp_entity._attr_native_step == 0.1

    @pytest.mark.asyncio
    async def test_temp_entity_native_value_scaled(self, mock_hass, mock_entry, mock_coordinator):
        """native_value should be raw API value ÷ 10."""
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        temp_entity = next(
            e for e in added_entities
            if isinstance(e, DucoboxBoxNumberEntity) and 'TempSupTgtZone1' in e._attr_unique_id
        )
        # Raw API value is 210, should display as 21.0
        assert temp_entity.native_value == 21.0

    @pytest.mark.asyncio
    async def test_temp_entity_set_value_scales_back(self, mock_hass, mock_entry, mock_coordinator):
        """Setting 21.5°C should send 215 to the API."""
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        temp_entity = next(
            e for e in added_entities
            if isinstance(e, DucoboxBoxNumberEntity) and 'TempSupTgtZone1' in e._attr_unique_id
        )
        await temp_entity.async_set_native_value(21.5)
        mock_coordinator.async_set_box_config.assert_called_with(
            'HeatRecovery', 'Bypass', 'TempSupTgtZone1', 215
        )

    @pytest.mark.asyncio
    async def test_non_temp_entity_has_no_unit(self, mock_hass, mock_entry, mock_coordinator):
        """Non-temperature entities should have no unit."""
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        filter_entity = next(
            e for e in added_entities
            if isinstance(e, DucoboxBoxNumberEntity) and 'TimeFilter' in e._attr_unique_id
        )
        assert filter_entity._attr_native_unit_of_measurement is None
        # Non-scaled: raw value should pass through directly
        assert filter_entity.native_value == 180


class TestNodeNumberEntity:

    @pytest.mark.asyncio
    async def test_native_value_reads_from_coordinator(self, mock_coordinator):
        """native_value reads from coordinator.data, not cached."""
        entity = DucoboxNodeNumberEntity(
            coordinator=mock_coordinator,
            node_id=1,
            param_key='FlowLvlAutoMin',
            device_info={'name': 'test', 'identifiers': set()},
            unique_id='test-1-FlowLvlAutoMin',
            min_value=10, max_value=80, step=5,
        )

        assert entity.native_value == 30

    @pytest.mark.asyncio
    async def test_native_value_returns_none_if_missing(self, mock_coordinator):
        entity = DucoboxNodeNumberEntity(
            coordinator=mock_coordinator,
            node_id=999,
            param_key='Missing',
            device_info={'name': 'test', 'identifiers': set()},
            unique_id='test-missing',
            min_value=0, max_value=100, step=1,
        )
        assert entity.native_value is None

    @pytest.mark.asyncio
    async def test_set_value_calls_coordinator(self, mock_coordinator):
        entity = DucoboxNodeNumberEntity(
            coordinator=mock_coordinator,
            node_id=3,
            param_key='Co2SetPoint',
            device_info={'name': 'test', 'identifiers': set()},
            unique_id='test-3-Co2SetPoint',
            min_value=0, max_value=2000, step=10,
        )

        await entity.async_set_native_value(1200)
        mock_coordinator.async_set_value.assert_called_once_with(3, 'Co2SetPoint', 1200)
        mock_coordinator.async_request_refresh.assert_called_once()


class TestBoxNumberEntity:

    @pytest.mark.asyncio
    async def test_native_value_reads_from_coordinator(self, mock_coordinator):
        entity = DucoboxBoxNumberEntity(
            coordinator=mock_coordinator,
            module='HeatRecovery',
            submodule='Bypass',
            param_key='TimeFilter',
            device_info={'name': 'test', 'identifiers': set()},
            unique_id='test-config-HeatRecovery-Bypass-TimeFilter',
            name='HeatRecovery Bypass TimeFilter',
            min_value=90, max_value=360, step=1,
        )
        assert entity.native_value == 180

    @pytest.mark.asyncio
    async def test_set_value_calls_coordinator(self, mock_coordinator):
        entity = DucoboxBoxNumberEntity(
            coordinator=mock_coordinator,
            module='HeatRecovery',
            submodule='Bypass',
            param_key='TimeFilter',
            device_info={'name': 'test', 'identifiers': set()},
            unique_id='test-config-HeatRecovery-Bypass-TimeFilter',
            name='HeatRecovery Bypass TimeFilter',
            min_value=90, max_value=360, step=1,
        )

        await entity.async_set_native_value(200)
        mock_coordinator.async_set_box_config.assert_called_once_with(
            'HeatRecovery', 'Bypass', 'TimeFilter', 200
        )
        mock_coordinator.async_request_refresh.assert_called_once()
