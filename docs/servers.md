# Servers

Inventory CRUD for Linux hosts (Phase 2). Blueprint: `blueprints/servers.py`. Validation: `schemas/server.py` + `utils/servers.py`.

## Fields

| Field | Notes |
|-------|--------|
| Display name | Label in the UI |
| Hostname / IP | e.g. `127.0.0.1` or remote host |
| SSH port | Default `22` |
| Auth type | `local`, `password`, or `key` |
| SSH username | Required for remote auth |
| SSH password | Sensitive — never shown in HTML; blank on edit keeps existing |
| SSH key path | Local path to private key; `..` and shell metacharacters rejected |

## Add a server

1. Sign in → **Add server** (`/servers/new`)
2. Local machine: auth type **local**, hostname `127.0.0.1` or `localhost`
3. Remote Linux: auth **password** or **key**, plus username / secret / key path
4. Save — appears on the dashboard; live metrics load via `GET /api/servers/metrics`

## Edit / delete

- **Edit** from the card or detail page (password field stays blank on purpose)
- **Delete** is POST-only with a confirm dialog

## Routes

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `/servers/new` | Create |
| GET/POST | `/servers/<id>/edit` | Update |
| POST | `/servers/<id>/delete` | Delete |
| GET | `/servers/<id>` | Detail page |

## Security

- All server routes require login
- SSH passwords are not rendered in list, detail, edit forms, or JSON
- Public Marshmallow schema omits `ssh_password` / key material
- Key paths reject `..` and `;|&\`$`

## Tests

```bash
pytest tests/test_servers.py
```
