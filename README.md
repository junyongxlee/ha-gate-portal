# Gate Portal

Home Assistant custom integration that exposes a PIN-protected REST API for an external guest portal to control selected entities.

## Installation

### HACS (recommended)

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=junyongxlee&repository=ha-gate-portal&category=integration)

Or manually:

1. Install [HACS](https://hacs.xyz/docs/setup/download) if you have not already.
2. Open **HACS** → **⋮** → **Custom repositories**.
3. Add `https://github.com/junyongxlee/ha-gate-portal` with category **Integration** (not AppDaemon or Plugin).
4. In **HACS → Integrations**, find **Gate Portal** and click **Download**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services → Add integration** and search for **Gate Portal**.

> **Note:** Do not add this repo under **Settings → Add-ons → Add-on store → Repositories**. That store is only for Docker add-ons, not custom integrations.

### Manual install

1. Copy `custom_components/gate_portal/` into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration** and search for **Gate Portal**.

## Configuration

During setup you choose exposed entities, the guest PIN, and whether the portal is enabled. To change settings later, open **Settings → Devices & services → Gate Portal**, click the **⋮** menu on the integration card, and choose **Configure**.

- **Exposed entities** — devices guests can control via the API
- **Guest PIN** — required for API access
- **Portal enabled** — when off, the API returns unavailable
- **Allowed CORS origins** — only needed if the frontend calls Home Assistant directly from a browser

Gate Portal is a **service** integration: it exposes a REST API only and does not add devices or entities under the integration card.

## API

Base URL: `https://<ha-host>:8123`

### GET `/api/gate_portal/status`

Returns portal status and metadata for exposed entities.

PIN can be sent as:

- Query parameter: `?pin=1234`
- Header: `X-Gate-Portal-Pin: 1234`

Example:

```bash
curl -s "http://localhost:8123/api/gate_portal/status?pin=1234"
```

Response:

```json
{
  "enabled": true,
  "entities": [
    {
      "entity_id": "cover.gate",
      "name": "Front Gate",
      "domain": "cover",
      "actions": ["open", "close", "stop", "toggle"]
    }
  ]
}
```

### POST `/api/gate_portal/action`

Executes an action on an exposed entity.

```bash
curl -s -X POST "http://localhost:8123/api/gate_portal/action" \
  -H "Content-Type: application/json" \
  -d '{"pin":"1234","entity_id":"cover.gate","action":"open"}'
```

Response:

```json
{
  "success": true,
  "entity_id": "cover.gate",
  "action": "open"
}
```

### Error responses

| Status | Meaning |
|--------|---------|
| 401 | Missing or invalid PIN |
| 404 | Entity not in allowlist |
| 400 | Invalid request or unsupported action |
| 503 | Portal disabled (`{"enabled": false}`) |

## Manual smoke test

1. Install the integration and configure at least one entity with PIN `1234`.
2. Confirm status works:

   ```bash
   curl -s "http://localhost:8123/api/gate_portal/status?pin=1234"
   ```

3. Confirm invalid PIN is rejected:

   ```bash
   curl -s -o /dev/null -w "%{http_code}" "http://localhost:8123/api/gate_portal/status?pin=wrong"
   ```

   Expected: `401`

4. Trigger an action:

   ```bash
   curl -s -X POST "http://localhost:8123/api/gate_portal/action" \
     -H "Content-Type: application/json" \
     -d '{"pin":"1234","entity_id":"cover.gate","action":"open"}'
   ```

5. Disable the portal in integration settings and confirm status returns `503`.

6. If using a browser-hosted frontend that calls Home Assistant directly, add its origin under **Allowed CORS origins** and verify preflight:

   ```bash
   curl -s -X OPTIONS "http://localhost:8123/api/gate_portal/status" \
     -H "Origin: https://portal.example.com" \
     -H "Access-Control-Request-Method: GET" \
     -i
   ```
