"""Tests for select.py — select platform entities."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from custom_components.ducobox_connectivity_board.select import (
    async_setup_entry,
    DucoboxActionSelectEntity,
    _humanize_action,
)
from custom_components.ducobox_connectivity_board.const import DOMAIN


@pytest.fixture
def mock_coordinator(coordinator_data):
    coord = MagicMock()
    coord.data = coordinator_data
    coord.last_update_success = True
    coord.async_set_ventilation_state = AsyncMock()
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


class TestHumanizeAction:

    def test_set_ventilation_state(self):
        assert _humanize_action('SetVentilationState') == 'Ventilation State'

    def test_set_parent(self):
        assert _humanize_action('SetParent') == 'Parent'


class TestSelectSetupEntry:

    @pytest.mark.asyncio
    async def test_creates_select_entities(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        assert len(added_entities) > 0
        for entity in added_entities:
            assert isinstance(entity, DucoboxActionSelectEntity)

    @pytest.mark.asyncio
    async def test_creates_one_per_node_with_enum(self, mock_hass, mock_entry, mock_coordinator):
        """Each node with a SetVentilationState Enum action gets a select entity."""
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        # Fixture has 2 nodes with SetVentilationState
        assert len(added_entities) == 2

    @pytest.mark.asyncio
    async def test_unique_ids(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        unique_ids = [e._attr_unique_id for e in added_entities]
        assert len(unique_ids) == len(set(unique_ids))

    @pytest.mark.asyncio
    async def test_current_option_from_coordinator(self, mock_hass, mock_entry, mock_coordinator):
        """current_option reads from coordinator.data nodes."""
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        # Node 1 has Ventilation.State.Val = 'AUTO'
        node1_entity = next(e for e in added_entities if e._node_id == 1)
        assert node1_entity.current_option == 'AUTO'

    @pytest.mark.asyncio
    async def test_select_option_calls_coordinator(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        entity = added_entities[0]
        await entity.async_select_option('MAN1')

        mock_coordinator.async_set_ventilation_state.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_entities_when_no_action_nodes(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        mock_coordinator.data['action_nodes'] = {'Nodes': []}
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        assert len(added_entities) == 0
