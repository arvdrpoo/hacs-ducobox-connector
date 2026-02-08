"""Tests for button.py — button platform entities."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from custom_components.ducobox_connectivity_board.button import (
    async_setup_entry,
    DucoboxButtonEntity,
    BOX_BUTTONS,
)
from custom_components.ducobox_connectivity_board.const import DOMAIN


@pytest.fixture
def mock_coordinator(coordinator_data):
    coord = MagicMock()
    coord.data = coordinator_data
    coord.last_update_success = True
    coord.async_execute_action = AsyncMock()
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


class TestButtonSetupEntry:

    @pytest.mark.asyncio
    async def test_creates_button_entities(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        assert len(added_entities) > 0
        for entity in added_entities:
            assert isinstance(entity, DucoboxButtonEntity)

    @pytest.mark.asyncio
    async def test_only_creates_available_actions(self, mock_hass, mock_entry, mock_coordinator):
        """Only actions present in the API response are created."""
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        # The fixture has 5 actions: ResetFilterTimeRemain, UpdateNodeData,
        # ReconnectWifi, ScanWifi, RebootBox
        # But BOX_BUTTONS only defines 4 safe ones (no RebootBox)
        assert len(added_entities) == 4

    @pytest.mark.asyncio
    async def test_skips_on_unknown_mac(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        mock_coordinator.data['info']['General']['Lan']['Mac'] = {'Val': None}
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        assert len(added_entities) == 0

    @pytest.mark.asyncio
    async def test_unique_ids(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        unique_ids = [e._attr_unique_id for e in added_entities]
        assert len(unique_ids) == len(set(unique_ids))

    @pytest.mark.asyncio
    async def test_press_calls_execute_action(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        # Find the ResetFilterTimeRemain button
        reset_btn = next(e for e in added_entities if 'reset_filter' in e._attr_unique_id)
        await reset_btn.async_press()

        mock_coordinator.async_execute_action.assert_called_once_with('ResetFilterTimeRemain')

    @pytest.mark.asyncio
    async def test_no_entities_when_no_actions(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        mock_coordinator.data['action'] = {}
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        assert len(added_entities) == 0
