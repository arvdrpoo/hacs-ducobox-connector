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


@dataclass(frozen=True, kw_only=True)
class DucoboxSensorEntityDescription(SensorEntityDescription):
    """Describes a Ducobox sensor entity."""

    value_fn: Callable[[dict], float | None]
    data_path: tuple[str, ...] | None = None  # Path to check for sensor existence


@dataclass(frozen=True, kw_only=True)
class DucoboxNodeSensorEntityDescription(SensorEntityDescription):
    """Describes a Ducobox node sensor entity."""

    value_fn: Callable[[dict], float | None]
    sensor_key: str
    node_type: str
    data_path: tuple[str, ...] | None = None  # Path to check for sensor existence in node data


SENSORS: tuple[DucoboxSensorEntityDescription, ...] = (
    # Temperature sensors
    # relevant ducobox documentation: https://www.duco.eu/Wes/CDN/1/Attachments/installation-guide-DucoBox-Energy-Comfort-(Plus)-(en)_638635518879333838.pdf
    # Oda = outdoor -> box
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
    # Sup = box -> house
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
    # Eta = house -> box
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
    # Eha = box -> outdoor
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
    # Fan speed sensors
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
    # Pressure sensors
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
    # Wi-Fi signal strength
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
    # Device uptime
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
    # Filter time remaining
    DucoboxSensorEntityDescription(
        key="TimeFilterRemain",
        name="Filter Time Remaining",
        native_unit_of_measurement=UnitOfTime.DAYS,  # Assuming the value is in days
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DURATION,
        value_fn=lambda data: process_timefilterremain(
            safe_get(data, 'info', 'HeatRecovery', 'General', 'TimeFilterRemain', 'Val')
        ),
        data_path=('info', 'HeatRecovery', 'General', 'TimeFilterRemain'),
    ),
    # Bypass position
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
    # Add additional sensors here if needed
)

# Define sensors for nodes based on their type
NODE_SENSORS: dict[str, list[DucoboxNodeSensorEntityDescription]] = {
    'BOX': [
        DucoboxNodeSensorEntityDescription(
            key='Mode',
            name='Ventilation Mode',
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'Mode')),
            sensor_key='Mode',
            node_type='BOX',
            data_path=('Ventilation', 'Mode'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='State',
            name='Ventilation State',
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'State')),
            sensor_key='State',
            node_type='BOX',
            data_path=('Ventilation', 'State'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='FlowLvlTgt',
            name='Flow Level Target',
            native_unit_of_measurement=PERCENTAGE,
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'FlowLvlTgt')),
            sensor_key='FlowLvlTgt',
            node_type='BOX',
            data_path=('Ventilation', 'FlowLvlTgt'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='TimeStateRemain',
            name='Time State Remaining',
            native_unit_of_measurement=UnitOfTime.SECONDS,
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'TimeStateRemain')),
            sensor_key='TimeStateRemain',
            node_type='BOX',
            data_path=('Ventilation', 'TimeStateRemain'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='TimeStateEnd',
            name='Time State End',
            native_unit_of_measurement=UnitOfTime.SECONDS,
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'TimeStateEnd')),
            sensor_key='TimeStateEnd',
            node_type='BOX',
            data_path=('Ventilation', 'TimeStateEnd'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Temp',
            name='Temperature',
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            value_fn=lambda node: process_node_temperature(
                extract_val(safe_get(node, 'Sensor', 'Temp'))
            ),
            sensor_key='Temp',
            node_type='BOX',
            data_path=('Sensor', 'Temp'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Rh',
            name='Relative Humidity',
            native_unit_of_measurement=PERCENTAGE,
            device_class=SensorDeviceClass.HUMIDITY,
            value_fn=lambda node: process_node_humidity(
                extract_val(safe_get(node, 'Sensor', 'Rh'))
            ),
            sensor_key='Rh',
            node_type='BOX',
            data_path=('Sensor', 'Rh'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='IaqRh',
            name='Humidity Air Quality',
            native_unit_of_measurement=PERCENTAGE,
            value_fn=lambda node: process_node_iaq(
                extract_val(safe_get(node, 'Sensor', 'IaqRh'))
            ),
            sensor_key='IaqRh',
            node_type='BOX',
            data_path=('Sensor', 'IaqRh'),
        ),
    ],
    'UCCO2': [
        DucoboxNodeSensorEntityDescription(
            key='Temp',
            name='Temperature',
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            value_fn=lambda node: process_node_temperature(
                extract_val(safe_get(node, 'Sensor', 'Temp'))
            ),
            sensor_key='Temp',
            node_type='UCCO2',
            data_path=('Sensor', 'Temp'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Co2',
            name='CO₂',
            native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
            device_class=SensorDeviceClass.CO2,
            value_fn=lambda node: process_node_co2(
                extract_val(safe_get(node, 'Sensor', 'Co2'))
            ),
            sensor_key='Co2',
            node_type='UCCO2',
            data_path=('Sensor', 'Co2'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='IaqCo2',
            name='CO₂ Air Quality',
            native_unit_of_measurement=PERCENTAGE,
            value_fn=lambda node: process_node_iaq(
                extract_val(safe_get(node, 'Sensor', 'IaqCo2'))
            ),
            sensor_key='IaqCo2',
            node_type='UCCO2',
            data_path=('Sensor', 'IaqCo2'),
        ),
    ],
    'BSRH': [
        DucoboxNodeSensorEntityDescription(
            key='Temp',
            name='Temperature',
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            value_fn=lambda node: process_node_temperature(
                extract_val(safe_get(node, 'Sensor', 'Temp'))
            ),
            sensor_key='Temp',
            node_type='BSRH',
            data_path=('Sensor', 'Temp'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Rh',
            name='Relative Humidity',
            native_unit_of_measurement=PERCENTAGE,
            device_class=SensorDeviceClass.HUMIDITY,
            value_fn=lambda node: process_node_humidity(
                extract_val(safe_get(node, 'Sensor', 'Rh'))
            ),
            sensor_key='Rh',
            node_type='BSRH',
            data_path=('Sensor', 'Rh'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='IaqRh',
            name='Humidity Air Quality',
            native_unit_of_measurement=PERCENTAGE,
            value_fn=lambda node: process_node_iaq(
                extract_val(safe_get(node, 'Sensor', 'IaqRh'))
            ),
            sensor_key='IaqRh',
            node_type='BSRH',
            data_path=('Sensor', 'IaqRh'),
        ),
    ],
    'VLVRH': [
        DucoboxNodeSensorEntityDescription(
            key='State',
            name='Ventilation State',
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'State')),
            sensor_key='State',
            node_type='VLVRH',
            data_path=('Ventilation', 'State'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='TimeStateRemain',
            name='Time State Remaining',
            native_unit_of_measurement=UnitOfTime.SECONDS,
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'TimeStateRemain')),
            sensor_key='TimeStateRemain',
            node_type='VLVRH',
            data_path=('Ventilation', 'TimeStateRemain'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='TimeStateEnd',
            name='Time State End',
            native_unit_of_measurement=UnitOfTime.SECONDS,
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'TimeStateEnd')),
            sensor_key='TimeStateEnd',
            node_type='VLVRH',
            data_path=('Ventilation', 'TimeStateEnd'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Mode',
            name='Ventilation Mode',
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'Mode')),
            sensor_key='Mode',
            node_type='VLVRH',
            data_path=('Ventilation', 'Mode'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='FlowLvlTgt',
            name='Flow Level Target',
            native_unit_of_measurement=PERCENTAGE,
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'FlowLvlTgt')),
            sensor_key='FlowLvlTgt',
            node_type='VLVRH',
            data_path=('Ventilation', 'FlowLvlTgt'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='IaqRh',
            name='Humidity Air Quality',
            native_unit_of_measurement=PERCENTAGE,
            value_fn=lambda node: process_node_iaq(
                extract_val(safe_get(node, 'Sensor', 'IaqRh'))
            ),
            sensor_key='IaqRh',
            node_type='VLVRH',
            data_path=('Sensor', 'IaqRh'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Rh',
            name='Relative Humidity',
            native_unit_of_measurement=PERCENTAGE,
            device_class=SensorDeviceClass.HUMIDITY,
            value_fn=lambda node: process_node_humidity(
                extract_val(safe_get(node, 'Sensor', 'Rh'))
            ),
            sensor_key='Rh',
            node_type='VLVRH',
            data_path=('Sensor', 'Rh'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Temp',
            name='Temperature',
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            value_fn=lambda node: process_node_temperature(
                extract_val(safe_get(node, 'Sensor', 'Temp'))
            ),
            sensor_key='Temp',
            node_type='VLVRH',
            data_path=('Sensor', 'Temp'),
        ),
    ],
    'VLVCO2': [
        DucoboxNodeSensorEntityDescription(
            key='State',
            name='Ventilation State',
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'State')),
            sensor_key='State',
            node_type='VLVCO2',
            data_path=('Ventilation', 'State'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='TimeStateRemain',
            name='Time State Remaining',
            native_unit_of_measurement=UnitOfTime.SECONDS,
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'TimeStateRemain')),
            sensor_key='TimeStateRemain',
            node_type='VLVCO2',
            data_path=('Ventilation', 'TimeStateRemain'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='TimeStateEnd',
            name='Time State End',
            native_unit_of_measurement=UnitOfTime.SECONDS,
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'TimeStateEnd')),
            sensor_key='TimeStateEnd',
            node_type='VLVCO2',
            data_path=('Ventilation', 'TimeStateEnd'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Mode',
            name='Ventilation Mode',
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'Mode')),
            sensor_key='Mode',
            node_type='VLVCO2',
            data_path=('Ventilation', 'Mode'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='FlowLvlTgt',
            name='Flow Level Target',
            native_unit_of_measurement=PERCENTAGE,
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'FlowLvlTgt')),
            sensor_key='FlowLvlTgt',
            node_type='VLVCO2',
            data_path=('Ventilation', 'FlowLvlTgt'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Co2',
            name='CO₂',
            native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
            device_class=SensorDeviceClass.CO2,
            value_fn=lambda node: process_node_co2(
                extract_val(safe_get(node, 'Sensor', 'Co2'))
            ),
            sensor_key='Co2',
            node_type='VLVCO2',
            data_path=('Sensor', 'Co2'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='IaqCo2',
            name='CO₂ Air Quality',
            native_unit_of_measurement=PERCENTAGE,
            value_fn=lambda node: process_node_iaq(
                extract_val(safe_get(node, 'Sensor', 'IaqCo2'))
            ),
            sensor_key='IaqCo2',
            node_type='VLVCO2',
            data_path=('Sensor', 'IaqCo2'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Temp',
            name='Temperature',
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            value_fn=lambda node: process_node_temperature(
                extract_val(safe_get(node, 'Sensor', 'Temp'))
            ),
            sensor_key='Temp',
            node_type='VLVCO2',
            data_path=('Sensor', 'Temp'),
        ),
    ],
    'VLVCO2RH': [
        DucoboxNodeSensorEntityDescription(
            key='State',
            name='Ventilation State',
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'State')),
            sensor_key='State',
            node_type='VLVCO2RH',
            data_path=('Ventilation', 'State'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='TimeStateRemain',
            name='Time State Remaining',
            native_unit_of_measurement=UnitOfTime.SECONDS,
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'TimeStateRemain')),
            sensor_key='TimeStateRemain',
            node_type='VLVCO2RH',
            data_path=('Ventilation', 'TimeStateRemain'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='TimeStateEnd',
            name='Time State End',
            native_unit_of_measurement=UnitOfTime.SECONDS,
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'TimeStateEnd')),
            sensor_key='TimeStateEnd',
            node_type='VLVCO2RH',
            data_path=('Ventilation', 'TimeStateEnd'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Mode',
            name='Ventilation Mode',
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'Mode')),
            sensor_key='Mode',
            node_type='VLVCO2RH',
            data_path=('Ventilation', 'Mode'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='FlowLvlTgt',
            name='Flow Level Target',
            native_unit_of_measurement=PERCENTAGE,
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'FlowLvlTgt')),
            sensor_key='FlowLvlTgt',
            node_type='VLVCO2RH',
            data_path=('Ventilation', 'FlowLvlTgt'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Co2',
            name='CO₂',
            native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
            device_class=SensorDeviceClass.CO2,
            value_fn=lambda node: process_node_co2(
                extract_val(safe_get(node, 'Sensor', 'Co2'))
            ),
            sensor_key='Co2',
            node_type='VLVCO2RH',
            data_path=('Sensor', 'Co2'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='IaqCo2',
            name='CO₂ Air Quality',
            native_unit_of_measurement=PERCENTAGE,
            value_fn=lambda node: process_node_iaq(
                extract_val(safe_get(node, 'Sensor', 'IaqCo2'))
            ),
            sensor_key='IaqCo2',
            node_type='VLVCO2RH',
            data_path=('Sensor', 'IaqCo2'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Rh',
            name='Relative Humidity',
            native_unit_of_measurement=PERCENTAGE,
            device_class=SensorDeviceClass.HUMIDITY,
            value_fn=lambda node: process_node_humidity(
                extract_val(safe_get(node, 'Sensor', 'Rh'))
            ),
            sensor_key='Rh',
            node_type='VLVCO2RH',
            data_path=('Sensor', 'Rh'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='IaqRh',
            name='Humidity Air Quality',
            native_unit_of_measurement=PERCENTAGE,
            value_fn=lambda node: process_node_iaq(
                extract_val(safe_get(node, 'Sensor', 'IaqRh'))
            ),
            sensor_key='IaqRh',
            node_type='VLVCO2RH',
            data_path=('Sensor', 'IaqRh'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Temp',
            name='Temperature',
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            value_fn=lambda node: process_node_temperature(
                extract_val(safe_get(node, 'Sensor', 'Temp'))
            ),
            sensor_key='Temp',
            node_type='VLVCO2RH',
            data_path=('Sensor', 'Temp'),
        ),
    ],
    'VLV': [
        DucoboxNodeSensorEntityDescription(
            key='State',
            name='Ventilation State',
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'State')),
            sensor_key='State',
            node_type='VLV',
            data_path=('Ventilation', 'State'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Mode',
            name='Ventilation Mode',
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'Mode')),
            sensor_key='Mode',
            node_type='VLV',
            data_path=('Ventilation', 'Mode'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='FlowLvlTgt',
            name='Flow Level Target',
            native_unit_of_measurement=PERCENTAGE,
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'FlowLvlTgt')),
            sensor_key='FlowLvlTgt',
            node_type='VLV',
            data_path=('Ventilation', 'FlowLvlTgt'),
        ),
    ],
    'SWITCH': [
        DucoboxNodeSensorEntityDescription(
            key='State',
            name='Ventilation State',
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'State')),
            sensor_key='State',
            node_type='SWITCH',
            data_path=('Ventilation', 'State'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Mode',
            name='Ventilation Mode',
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'Mode')),
            sensor_key='Mode',
            node_type='SWITCH',
            data_path=('Ventilation', 'Mode'),
        ),
    ],
    'UCBAT': [
        DucoboxNodeSensorEntityDescription(
            key='State',
            name='Ventilation State',
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'State')),
            sensor_key='State',
            node_type='UCBAT',
            data_path=('Ventilation', 'State'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='TimeStateRemain',
            name='Time State Remaining',
            native_unit_of_measurement=UnitOfTime.SECONDS,
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'TimeStateRemain')),
            sensor_key='TimeStateRemain',
            node_type='UCBAT',
            data_path=('Ventilation', 'TimeStateRemain'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='TimeStateEnd',
            name='Time State End',
            native_unit_of_measurement=UnitOfTime.SECONDS,
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'TimeStateEnd')),
            sensor_key='TimeStateEnd',
            node_type='UCBAT',
            data_path=('Ventilation', 'TimeStateEnd'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Mode',
            name='Ventilation Mode',
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'Mode')),
            sensor_key='Mode',
            node_type='UCBAT',
            data_path=('Ventilation', 'Mode'),
        ),
    ],
    'UCRH': [
        DucoboxNodeSensorEntityDescription(
            key='State',
            name='Ventilation State',
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'State')),
            sensor_key='State',
            node_type='UCRH',
            data_path=('Ventilation', 'State'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='TimeStateRemain',
            name='Time State Remaining',
            native_unit_of_measurement=UnitOfTime.SECONDS,
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'TimeStateRemain')),
            sensor_key='TimeStateRemain',
            node_type='UCRH',
            data_path=('Ventilation', 'TimeStateRemain'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='TimeStateEnd',
            name='Time State End',
            native_unit_of_measurement=UnitOfTime.SECONDS,
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'TimeStateEnd')),
            sensor_key='TimeStateEnd',
            node_type='UCRH',
            data_path=('Ventilation', 'TimeStateEnd'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Mode',
            name='Ventilation Mode',
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'Mode')),
            sensor_key='Mode',
            node_type='UCRH',
            data_path=('Ventilation', 'Mode'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='FlowLvlTgt',
            name='Flow Level Target',
            native_unit_of_measurement=PERCENTAGE,
            value_fn=lambda node: extract_val(safe_get(node, 'Ventilation', 'FlowLvlTgt')),
            sensor_key='FlowLvlTgt',
            node_type='UCRH',
            data_path=('Ventilation', 'FlowLvlTgt'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='IaqRh',
            name='Humidity Air Quality',
            native_unit_of_measurement=PERCENTAGE,
            value_fn=lambda node: process_node_iaq(
                extract_val(safe_get(node, 'Sensor', 'IaqRh'))
            ),
            sensor_key='IaqRh',
            node_type='UCRH',
            data_path=('Sensor', 'IaqRh'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Rh',
            name='Relative Humidity',
            native_unit_of_measurement=PERCENTAGE,
            device_class=SensorDeviceClass.HUMIDITY,
            value_fn=lambda node: process_node_humidity(
                extract_val(safe_get(node, 'Sensor', 'Rh'))
            ),
            sensor_key='Rh',
            node_type='UCRH',
            data_path=('Sensor', 'Rh'),
        ),
        DucoboxNodeSensorEntityDescription(
            key='Temp',
            name='Temperature',
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            value_fn=lambda node: process_node_temperature(
                extract_val(safe_get(node, 'Sensor', 'Temp'))
            ),
            sensor_key='Temp',
            node_type='UCRH',
            data_path=('Sensor', 'Temp'),
        ),
    ],
    # Add other node types and their sensors if needed
}
