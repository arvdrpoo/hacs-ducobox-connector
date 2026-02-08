"""Tests for switch.py — boolean config parameter switch entities."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from custom_components.ducobox_connectivity_board.switch import (
    async_setup_entry,
    DucoboxBoxSwitchEntity,
    _is_boolean_param,
)
from custom_components.ducobox_connectivity_board.const import DOMAIN


@pytest.fixture
def mock_coordinator(coordinator_data):
    coord = MagicMock()
    coord.data = coordinator_data
    coord.last_update_success = True
    coord.async_set_box_config = AsyncMock()
    coord.async_request_refresh = AsyncMock()
    return coord


@pytest.fixture
def mock_hass(mock_coordinator):
    hass = MagicMock()
    entry_data = {'coordinator': mock_coordinator}
    hass.data = {DOMAIN: {'test_entry': entry_data}}
    return hass, entry_data


@pytest.fixture
def mock_entry():
    entry = MagicMock()
    entry.entry_id = 'test_entry'
    return entry


class TestIsBooleanParam:
    def test_valid_boolean(self):
        assert _is_boolean_param({'Val': 0, 'Min': 0, 'Inc': 1, 'Max': 1}) is True

    def test_not_boolean_range(self):
        assert _is_boolean_param({'Val': 0, 'Min': 0, 'Inc': 1, 'Max': 2}) is False

    def test_not_number_param(self):
        assert _is_boolean_param({'Val': 'foo'}) is False

    def test_min_not_zero(self):
        assert _is_boolean_param({'Val': 1, 'Min': 1, 'Inc': 1, 'Max': 1}) is False


class TestSwitchSetupEntry:

    @pytest.mark.asyncio
    async def test_creates_switch_entities(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        assert len(added_entities) > 0
        assert all(isinstance(e, DucoboxBoxSwitchEntity) for e in added_entities)

    @pytest.mark.asyncio
    async def test_boolean_params_become_switches(self, mock_hass, mock_entry, mock_coordinator):
        """All Min=0/Max=1 params outside skip lists should be switches."""
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        uids = {e._attr_unique_id for e in added_entities}
        # VentCool day-of-week enables
        assert any('EnableMonday' in uid for uid in uids)
        assert any('EnableSunday' in uid for uid in uids)
        # NightBoost enable
        assert any('NightBoost' in uid and 'Enable' in uid for uid in uids)
        # HeatRecovery booleans
        assert any('Adaptive' in uid for uid in uids)
        assert any('PassiveHouse' in uid for uid in uids)
        # Ventilation booleans
        assert any('TempDepEnable' in uid for uid in uids)
        assert any('GroundBound' in uid for uid in uids)
        # General.Time.Dst
        assert any('Dst' in uid for uid in uids)

    @pytest.mark.asyncio
    async def test_excludes_skipped_submodules(self, mock_hass, mock_entry, mock_coordinator):
        """Boolean params in skipped submodules should not appear."""
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        uids = {e._attr_unique_id for e in added_entities}
        # DowngradeAllow (Firmware.General) is skipped
        assert not any('DowngradeAllow' in uid for uid in uids)
        # Azure.Connection.Enable is skipped
        assert not any('Azure' in uid for uid in uids)

    @pytest.mark.asyncio
    async def test_unique_ids_unique(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        uids = [e._attr_unique_id for e in added_entities]
        assert len(uids) == len(set(uids))

    @pytest.mark.asyncio
    async def test_skips_on_unknown_mac(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        mock_coordinator.data['info']['General']['Lan']['Mac'] = {'Val': None}
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        assert len(added_entities) == 0


class TestBoxSwitchEntity:

    @pytest.mark.asyncio
    async def test_is_on_reads_from_coordinator(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        # Find EnableMonday (Val=0 → off)
        monday = next(e for e in added_entities if 'EnableMonday' in e._attr_unique_id)
        assert monday.is_on is False

        # Find TempDepEnable (Val=1 → on)
        temp_dep = next(e for e in added_entities if 'TempDepEnable' in e._attr_unique_id)
        assert temp_dep.is_on is True

    @pytest.mark.asyncio
    async def test_turn_on(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        monday = next(e for e in added_entities if 'EnableMonday' in e._attr_unique_id)
        await monday.async_turn_on()

        mock_coordinator.async_set_box_config.assert_called_with(
            'VentCool', 'General', 'EnableMonday', 1
        )

    @pytest.mark.asyncio
    async def test_turn_off(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        temp_dep = next(e for e in added_entities if 'TempDepEnable' in e._attr_unique_id)
        await temp_dep.async_turn_off()

        mock_coordinator.async_set_box_config.assert_called_with(
            'Ventilation', 'Ctrl', 'TempDepEnable', 0
        )
