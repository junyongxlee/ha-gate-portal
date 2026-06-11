"""Entity action resolution and service calls."""

from __future__ import annotations

from homeassistant.core import HomeAssistant, State

from .const import ACTION_SERVICES, DOMAIN_ACTIONS


def get_entity_domain(entity_id: str) -> str:
    """Return the domain portion of an entity ID."""
    return entity_id.split(".", 1)[0]


def get_actions_for_entity(entity_id: str) -> list[str]:
    """Return supported actions for an entity based on its domain."""
    domain = get_entity_domain(entity_id)
    return list(DOMAIN_ACTIONS.get(domain, []))


def build_entity_info(hass: HomeAssistant, entity_id: str) -> dict[str, object] | None:
    """Build public entity metadata for the status endpoint."""
    state = hass.states.get(entity_id)
    if state is None:
        return None

    domain = get_entity_domain(entity_id)
    actions = get_actions_for_entity(entity_id)
    if not actions:
        return None

    return {
        "entity_id": entity_id,
        "name": state.attributes.get("friendly_name", entity_id),
        "domain": domain,
        "actions": actions,
    }


def validate_action(entity_id: str, action: str) -> tuple[str, str] | None:
    """Return (service_domain, service_name) if action is valid for entity."""
    domain = get_entity_domain(entity_id)
    allowed = DOMAIN_ACTIONS.get(domain, [])
    if action not in allowed:
        return None
    return ACTION_SERVICES.get((domain, action))


async def call_entity_action(
    hass: HomeAssistant, entity_id: str, action: str
) -> None:
    """Call the Home Assistant service for an entity action."""
    service = validate_action(entity_id, action)
    if service is None:
        raise ValueError(f"Invalid action '{action}' for entity '{entity_id}'")

    service_domain, service_name = service
    await hass.services.async_call(
        service_domain,
        service_name,
        {"entity_id": entity_id},
        blocking=True,
    )


def entity_exists(hass: HomeAssistant, entity_id: str) -> bool:
    """Return whether an entity currently has state."""
    return isinstance(hass.states.get(entity_id), State)
