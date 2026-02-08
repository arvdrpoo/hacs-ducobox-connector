"""Tests for sensor.py — the HA platform setup entry point.

We test async_setup_entry by mocking the coordinator and verifying that
the correct entities are created for both box-level and node-level sensors.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from custom_components.ducobox_connectivity_board.sensor import async_setup_entry
from custom_components.ducobox_connectivity_board.model.coordinator import (
    DucoboxSensorEntity,
    DucoboxNodeSensorEntity,
)
from custom_components.ducobox_connectivity_board.model.devices import SENSORS
from custom_components.ducobox_connectivity_board.const import DOMAIN


@pytest.fixture
def mock_coordinator(coordinator_data):
    """A coordinator-like object with realistic data."""
    coord = MagicMock()
    coord.data = coordinator_data
    coord.last_update_success = True
    return coord


@pytest.fixture
def mock_hass(mock_coordinator):
    """Mock hass with coordinator in data."""
    hass = MagicMock()
    entry_id = 'test_entry_123'
    hass.data = {DOMAIN: {entry_id: {'coordinator': mock_coordinator}}}
    return hass, entry_id


@pytest.fixture
def mock_entry(mock_hass):
    """Mock ConfigEntry."""
    hass, entry_id = mock_hass
    entry = MagicMock()
    entry.entry_id = entry_id
    return entry


# ── async_setup_entry ─────────────────────────────────────────────────

class TestAsyncSetupEntry:

    @pytest.mark.asyncio
    async def test_creates_entities(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        def capture_entities(entities):
            added_entities.extend(entities)

        await async_setup_entry(hass, mock_entry, capture_entities)

        assert len(added_entities) > 0

    @pytest.mark.asyncio
    async def test_creates_box_sensors(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        box_entities = [e for e in added_entities if isinstance(e, DucoboxSensorEntity)]
        # Should have one entity per SENSORS entry that exists in the data
        assert len(box_entities) > 0
        assert len(box_entities) <= len(SENSORS)

    @pytest.mark.asyncio
    async def test_creates_node_sensors(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        node_entities = [e for e in added_entities if isinstance(e, DucoboxNodeSensorEntity)]
        # 5 nodes in the fixture; each with varying numbers of sensors
        assert len(node_entities) > 0

    @pytest.mark.asyncio
    async def test_box_entities_have_unique_ids(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        box_entities = [e for e in added_entities if isinstance(e, DucoboxSensorEntity)]
        unique_ids = [e._attr_unique_id for e in box_entities]
        assert len(unique_ids) == len(set(unique_ids)), "Duplicate unique IDs found"

    @pytest.mark.asyncio
    async def test_node_entities_have_unique_ids(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        node_entities = [e for e in added_entities if isinstance(e, DucoboxNodeSensorEntity)]
        unique_ids = [e._attr_unique_id for e in node_entities]
        assert len(unique_ids) == len(set(unique_ids)), "Duplicate unique IDs found"

    @pytest.mark.asyncio
    async def test_skips_sensors_missing_from_data(self, mock_hass, mock_entry, mock_coordinator):
        """Sensors whose data_path doesn't exist in the API response are skipped."""
        hass, _ = mock_hass
        # Remove some data to test the skip logic
        del mock_coordinator.data['info']['NightBoost']

        added_entities = []
        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        box_keys = {e.entity_description.key for e in added_entities
                    if isinstance(e, DucoboxSensorEntity)}
        assert 'NightBoostTempOutsideAvg' not in box_keys
        assert 'NightBoostFlowLvlReqZone1' not in box_keys
        assert 'NightBoostTempOutsideAvgThs' not in box_keys
        assert 'NightBoostTempOutside' not in box_keys
        assert 'NightBoostTempComfort' not in box_keys
        assert 'NightBoostTempZone1' not in box_keys

    @pytest.mark.asyncio
    async def test_returns_on_unknown_mac(self, mock_hass, mock_entry, mock_coordinator):
        """If MAC is unknown, no entities should be added."""
        hass, _ = mock_hass
        # Remove the MAC address
        mock_coordinator.data['info']['General']['Lan']['Mac'] = {'Val': None}

        added_entities = []
        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        # When mac is "unknown_mac" (because Val is None), setup returns early
        assert len(added_entities) == 0

    @pytest.mark.asyncio
    async def test_bsrh_node_has_sensors(self, mock_hass, mock_entry, mock_coordinator):
        """Regression test: BSRH nodes must have Temp, Rh, IaqRh sensors."""
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        # Find BSRH node entities (node 58)
        bsrh_entities = [
            e for e in added_entities
            if isinstance(e, DucoboxNodeSensorEntity) and e._node_id == 58
        ]
        bsrh_keys = {e.entity_description.sensor_key for e in bsrh_entities}

        assert 'Sensor_Temp' in bsrh_keys, "BSRH missing Temperature sensor"
        assert 'Sensor_Rh' in bsrh_keys, "BSRH missing Relative Humidity sensor"
        assert 'Sensor_IaqRh' in bsrh_keys, "BSRH missing Humidity IAQ sensor"

    @pytest.mark.asyncio
    async def test_ucco2_node_has_co2(self, mock_hass, mock_entry, mock_coordinator):
        """UCCO2 nodes must have CO₂ sensor."""
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        ucco2_entities = [
            e for e in added_entities
            if isinstance(e, DucoboxNodeSensorEntity) and e._node_id == 3
        ]
        ucco2_keys = {e.entity_description.sensor_key for e in ucco2_entities}

        assert 'Sensor_Co2' in ucco2_keys
        assert 'Sensor_IaqCo2' in ucco2_keys

    @pytest.mark.asyncio
    async def test_handles_no_nodes(self, mock_hass, mock_entry, mock_coordinator):
        """If no nodes in data, only box sensors are created."""
        hass, _ = mock_hass
        mock_coordinator.data['nodes'] = None

        added_entities = []
        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        node_entities = [e for e in added_entities if isinstance(e, DucoboxNodeSensorEntity)]
        box_entities = [e for e in added_entities if isinstance(e, DucoboxSensorEntity)]

        assert len(node_entities) == 0
        assert len(box_entities) > 0

    @pytest.mark.asyncio
    async def test_device_info_contains_model(self, mock_hass, mock_entry, mock_coordinator):
        hass, _ = mock_hass
        added_entities = []

        await async_setup_entry(hass, mock_entry, lambda e: added_entities.extend(e))

        box_entity = next(
            e for e in added_entities if isinstance(e, DucoboxSensorEntity)
        )
        di = box_entity._attr_device_info
        assert 'ENERGY' in di['model']
        assert 'COMFORT' in di['model']
