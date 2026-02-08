"""Tests for model/coordinator.py.

The coordinator depends on DucoPy and Home Assistant; both are mocked.
We test the data-fetching logic, mapping generation, and entity value
extraction.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from custom_components.ducobox_connectivity_board.model.coordinator import (
    DucoboxCoordinator,
    DucoboxSensorEntity,
    DucoboxNodeSensorEntity,
)
from custom_components.ducobox_connectivity_board.model.devices import (
    DucoboxSensorEntityDescription,
    DucoboxNodeSensorEntityDescription,
    SENSORS,
    discover_node_sensors,
)


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def mock_duco_client(api_info_response, api_nodes_response, api_config_nodes_response):
    """A MagicMock DucoPy client that returns realistic data."""
    client = MagicMock()

    def _raw_get(endpoint):
        if endpoint == '/info':
            return api_info_response
        elif endpoint == '/info/nodes':
            return {'Nodes': api_nodes_response}
        elif endpoint == '/config/nodes':
            return api_config_nodes_response
        elif endpoint == '/action/nodes':
            return {'Nodes': []}
        return {}

    client.raw_get = MagicMock(side_effect=_raw_get)
    client.raw_patch = MagicMock()
    client.change_action_node = MagicMock()
    return client


@pytest.fixture
def mock_hass():
    """A minimal mock Home Assistant instance."""
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock(side_effect=lambda fn, *a, **kw: fn(*a, **kw))
    return hass


@pytest.fixture
def coordinator(mock_hass, mock_duco_client):
    """A DucoboxCoordinator with mocked deps."""
    coord = DucoboxCoordinator(mock_hass, mock_duco_client)
    return coord


# ── _fetch_once_data ──────────────────────────────────────────────────

class TestFetchOnceData:

    def test_fetches_action_nodes(self, coordinator, mock_duco_client):
        result = coordinator._fetch_once_data()
        mock_duco_client.raw_get.assert_any_call('/action/nodes')
        assert 'action_nodes' in result

    def test_result_structure(self, coordinator):
        result = coordinator._fetch_once_data()
        assert isinstance(result['action_nodes'], dict)


# ── _fetch_data ───────────────────────────────────────────────────────

class TestFetchData:

    def test_fetches_all_endpoints(self, coordinator, mock_duco_client):
        # Must call _fetch_once_data first (simulates _async_setup)
        coordinator._static_data = coordinator._fetch_once_data()

        data = coordinator._fetch_data()

        mock_duco_client.raw_get.assert_any_call('/info')
        mock_duco_client.raw_get.assert_any_call('/info/nodes')
        mock_duco_client.raw_get.assert_any_call('/config/nodes')

    def test_data_contains_expected_keys(self, coordinator):
        coordinator._static_data = coordinator._fetch_once_data()
        data = coordinator._fetch_data()

        assert 'info' in data
        assert 'nodes' in data
        assert 'config_nodes' in data
        assert 'mappings' in data
        assert 'action_nodes' in data

    def test_nodes_is_list(self, coordinator, api_nodes_response):
        coordinator._static_data = coordinator._fetch_once_data()
        data = coordinator._fetch_data()

        assert isinstance(data['nodes'], list)
        assert len(data['nodes']) == len(api_nodes_response)

    def test_mappings_built_correctly(self, coordinator):
        coordinator._static_data = coordinator._fetch_once_data()
        data = coordinator._fetch_data()

        mappings = data['mappings']
        # Node 1 = BOX
        assert mappings['node_id_to_type'][1] == 'BOX'
        assert '1:BOX' == mappings['node_id_to_name'][1]

        # Node 3 = UCCO2
        assert mappings['node_id_to_type'][3] == 'UCCO2'

        # Node 58 = BSRH
        assert mappings['node_id_to_type'][58] == 'BSRH'

    def test_handles_empty_nodes(self, coordinator):
        coordinator._static_data = coordinator._fetch_once_data()
        coordinator.duco_client.raw_get = MagicMock(side_effect=lambda ep: {
            '/info': {},
            '/info/nodes': {},  # no 'Nodes' key
            '/config/nodes': {},
        }[ep])

        data = coordinator._fetch_data()
        assert data['nodes'] == []

    def test_raises_on_none_client(self, coordinator):
        coordinator._static_data = coordinator._fetch_once_data()
        coordinator.duco_client = None

        with pytest.raises(Exception, match="not initialized"):
            coordinator._fetch_data()


# ── DucoboxSensorEntity ──────────────────────────────────────────────

class TestDucoboxSensorEntity:

    @pytest.fixture
    def box_entity(self, coordinator, coordinator_data):
        """A box-level sensor entity for TempOda."""
        coordinator.data = coordinator_data
        coordinator.last_update_success = True

        desc = next(s for s in SENSORS if s.key == 'TempOda')
        device_info = {'name': 'test_device', 'identifiers': {('ducobox', 'test')}}

        return DucoboxSensorEntity(
            coordinator=coordinator,
            description=desc,
            device_info=device_info,
            unique_id='test-TempOda',
        )

    def test_native_value(self, box_entity):
        assert box_entity.native_value == pytest.approx(10.8)

    def test_available(self, box_entity):
        assert box_entity.available is True

    def test_unavailable(self, box_entity):
        box_entity.coordinator.last_update_success = False
        assert box_entity.available is False

    def test_unique_id(self, box_entity):
        assert box_entity._attr_unique_id == 'test-TempOda'

    def test_name_includes_device(self, box_entity):
        assert 'test_device' in box_entity._attr_name
        assert 'Outdoor Temperature' in box_entity._attr_name


# ── DucoboxNodeSensorEntity ──────────────────────────────────────────

class TestDucoboxNodeSensorEntity:

    @pytest.fixture
    def node_entity(self, coordinator, coordinator_data, api_nodes_response):
        """A node sensor entity for node 3 (UCCO2) CO₂ sensor."""
        coordinator.data = coordinator_data
        coordinator.last_update_success = True

        node = api_nodes_response[2]  # UCCO2
        descriptions = discover_node_sensors(node)
        desc = next(d for d in descriptions if d.sensor_key == 'Sensor_Co2')

        device_info = {'name': 'test_node', 'identifiers': {('ducobox', 'node3')}}

        return DucoboxNodeSensorEntity(
            coordinator=coordinator,
            node_id=3,
            description=desc,
            device_info=device_info,
            unique_id='test-node3-Sensor_Co2',
            device_id='test_device',
            node_name='test:3:UCCO2',
        )

    def test_native_value(self, node_entity):
        assert node_entity.native_value == 1056

    def test_native_value_missing_node(self, node_entity):
        """If the node disappears from the data, return None."""
        node_entity.coordinator.data['nodes'] = []
        assert node_entity.native_value is None

    def test_available(self, node_entity):
        assert node_entity.available is True

    def test_name_includes_node(self, node_entity):
        assert 'UCCO2' in node_entity._attr_name

    def test_node_id_stored(self, node_entity):
        assert node_entity._node_id == 3


# ── async_set_value ──────────────────────────────────────────────────

class TestAsyncSetValue:

    @pytest.mark.asyncio
    async def test_patches_config(self, coordinator, mock_duco_client, mock_hass):
        await coordinator.async_set_value(node_id=3, key='Co2SetPoint', value=1200)

        mock_duco_client.raw_patch.assert_called_once()
        call_args = mock_duco_client.raw_patch.call_args
        assert '/config/nodes/3' in call_args[0][0]
        # The JSON body should contain the key and rounded value
        import json
        body = json.loads(call_args[0][1])
        assert body['Co2SetPoint']['Val'] == 1200

    @pytest.mark.asyncio
    async def test_rounds_value(self, coordinator, mock_duco_client, mock_hass):
        await coordinator.async_set_value(node_id=1, key='FlowLvlAutoMin', value=35.7)

        body_str = mock_duco_client.raw_patch.call_args[0][1]
        import json
        body = json.loads(body_str)
        assert body['FlowLvlAutoMin']['Val'] == 36

    @pytest.mark.asyncio
    async def test_raises_on_failure(self, coordinator, mock_duco_client, mock_hass):
        mock_duco_client.raw_patch.side_effect = Exception("connection refused")

        with pytest.raises(Exception, match="connection refused"):
            await coordinator.async_set_value(1, 'Key', 10)


# ── async_set_ventilation_state ──────────────────────────────────────

class TestAsyncSetVentilationState:

    @pytest.mark.asyncio
    async def test_calls_change_action(self, coordinator, mock_duco_client, mock_hass):
        await coordinator.async_set_ventilation_state(
            node_id=1, option='MAN1', action='SetVentilationState'
        )

        mock_duco_client.change_action_node.assert_called_once_with(
            'SetVentilationState', 'MAN1', 1
        )

    @pytest.mark.asyncio
    async def test_raises_on_failure(self, coordinator, mock_duco_client, mock_hass):
        mock_duco_client.change_action_node.side_effect = Exception("timeout")

        with pytest.raises(Exception, match="timeout"):
            await coordinator.async_set_ventilation_state(1, 'MAN1', 'SetVentilationState')
