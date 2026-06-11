"""The Gate Portal integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .api import GatePortalActionView, GatePortalStatusView, RateLimiter
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = []


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Gate Portal integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gate Portal from a config entry."""
    domain_data = hass.data.setdefault(DOMAIN, {})

    if "rate_limiter" not in domain_data:
        rate_limiter = RateLimiter()
        hass.http.register_view(GatePortalStatusView(rate_limiter))
        hass.http.register_view(GatePortalActionView(rate_limiter))
        domain_data["rate_limiter"] = rate_limiter

    domain_data[entry.entry_id] = {"entry": entry}

    _LOGGER.debug("Gate Portal entry %s set up", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    domain_data = hass.data.get(DOMAIN)
    if domain_data:
        domain_data.pop(entry.entry_id, None)
        # Keep rate_limiter and registered views for options-flow reloads.

    _LOGGER.debug("Gate Portal entry %s unloaded", entry.entry_id)
    return True
