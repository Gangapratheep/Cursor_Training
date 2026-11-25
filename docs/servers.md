# Servers (Phase 2)

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

1. Sign in → **Add server**
2. For this machine: auth type **local**, hostname `127.0.0.1` or `localhost`
3. For remote Linux: auth **password** or **key**, plus username / secret / key path
4. Save — appears on the dashboard (names/hosts only; metrics come later)

## Edit / delete

- **Edit** from the dashboard row (password field stays blank on purpose)
- **Delete** is POST-only with a confirm dialog

## Security

- All server routes require login
- SSH passwords are not rendered in list or edit forms
- Key paths reject `..` and `;|&\`$`

## Tests

```bash
pytest tests/test_servers.py
```
