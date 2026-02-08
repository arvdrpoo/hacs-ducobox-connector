import logging
import urllib3
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from .const import DOMAIN
from ducopy import DucoPy
from .model.coordinator import DucoboxCoordinator

# The Ducobox uses a self-signed certificate; suppress the per-request warning.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_LOGGER = logging.getLogger(__name__)
_PLATFORMS = ['sensor', 'number', 'select', 'switch', 'button']


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Ducobox Connectivity Board integration."""
    _LOGGER.debug("Setting up Ducobox Connectivity Board integration")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ducobox from a config entry."""
    base_url = entry.data["base_url"]
    _LOGGER.debug(f"Base URL from config entry: {base_url}")

    try:
        duco_client = DucoPy(base_url=base_url, verify=False)
        coordinator = DucoboxCoordinator(hass, duco_client)
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.debug(f"DucoPy initialized with base URL: {base_url}")
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {'client': duco_client, 'coordinator': coordinator}
    except Exception as ex:
        _LOGGER.error("Could not connect to Ducobox: %s", ex)
        raise ConfigEntryNotReady from ex

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
