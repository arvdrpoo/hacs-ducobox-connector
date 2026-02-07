def safe_get(data, *keys):
    """Safely get nested keys from a dict."""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return None
    return data


def extract_val(data):
    """Extract 'Val' from a dict if present, otherwise return the data as-is."""
    if isinstance(data, dict) and 'Val' in data:
        return data['Val']
    return data

# Node-specific processing functions
def process_node_temperature(value):
    """Process node temperature values."""
    if value is not None:
        return value  # Assuming value is in Celsius
    return None

def process_node_humidity(value):
    """Process node humidity values."""
    if value is not None:
        return value  # Assuming value is in percentage
    return None

def process_node_co2(value):
    """Process node CO₂ values."""
    if value is not None:
        return value  # Assuming value is in ppm
    return None

def process_node_iaq(value):
    """Process node IAQ values."""
    if value is not None:
        return value  # Assuming value is in percentage
    return None

# Main sensor processing functions
def process_temperature(value):
    """Process temperature values by dividing by 10."""
    if value is not None:
        return value / 10.0  # Convert from tenths of degrees Celsius
    return None

def process_speed(value):
    """Process speed values."""
    if value is not None:
        return value  # Assuming value is already in RPM
    return None

def process_pressure(value):
    """Process pressure values."""
    if value is not None:
        # Shift decimal to the correct position.
        return float(value) * .1  # Assuming value is in Pa
    return None

def process_rssi(value):
    """Process Wi-Fi signal strength."""
    if value is not None:
        return value  # Assuming value is in dBm
    return None

def process_uptime(value):
    """Process device uptime."""
    if value is not None:
        return value  # Assuming value is in seconds
    return None

def process_timefilterremain(value):
    """Process filter time remaining."""
    if value is not None:
        return value  # Assuming value is in days
    return None

def process_bypass_position(value):
    """Process bypass position."""
    if value is not None:
        # Assuming value ranges from 0 to 100, where 100 is 100%
        return int(round(float(value), 0))
    return None
