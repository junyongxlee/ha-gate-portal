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
    rate_limiter = RateLimiter()
    status_view = GatePortalStatusView(rate_limiter)
    action_view = GatePortalActionView(rate_limiter)

    hass.http.register_view(status_view)
    hass.http.register_view(action_view)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "entry": entry,
        "rate_limiter": rate_limiter,
        "views": [status_view, action_view],
    }

    _LOGGER.debug("Gate Portal entry %s set up", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if data:
        for view in data.get("views", []):
            hass.http.async_unregister_view(view)

    if not hass.data.get(DOMAIN):
        hass.data.pop(DOMAIN, None)

    _LOGGER.debug("Gate Portal entry %s unloaded", entry.entry_id)
    return True
