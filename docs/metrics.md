# Metrics

Read-only collection for registered servers. Collectors: `metrics/`. API: `blueprints/api.py` (Flask-RESTful + Marshmallow).

No remote shell from the UI; no kill-process or firewall actions.

## Local collection (psutil)

Used when auth type is `local`, or hostname is `localhost` / `127.0.0.1` / `::1`.

| Field | Source |
|-------|--------|
| `cpu_percent` | `psutil.cpu_percent` |
| `memory` | `psutil.virtual_memory` |
| `network` | `psutil.net_io_counters` |
| `listening_ports` | `psutil.net_connections` (LISTEN only) |

## Remote collection (Paramiko / SSH)

Password or key auth. Connect timeout **8s**; command timeout **10s**.

**Host keys:** loads `~/.ssh/known_hosts` when present; unknown hosts are **rejected** by default (`RejectPolicy`). For a local demo that must accept first-time hosts, set `SSH_AUTO_ADD_HOST_KEYS=1` (MITM-prone — avoid in real environments). Passwords/keys are never logged or returned in JSON/HTML.

### Fixed commands (no user input interpolated)

| Purpose | Command |
|---------|---------|
| CPU | `cat /proc/stat` (two samples) |
| Memory | `cat /proc/meminfo` |
| Network | `cat /proc/net/dev` |
| Ports | `ss -lntuH` |

## Status meanings

| Status | Meaning |
|--------|---------|
| `ok` | Metrics collected |
| `unreachable` | Timeout / connection failure |
| `error` | Auth failure or other collection error (message sanitized/truncated) |

## API

All routes require login. Payloads never include SSH passwords or key material.

### One server

`GET /api/servers/<id>/metrics`

```json
{
  "server_id": 1,
  "status": "ok",
  "error": null,
  "collected_at": "2026-01-01T00:00:00+00:00",
  "cpu_percent": 12.5,
  "memory": {"used_bytes": 1, "total_bytes": 2, "percent": 50.0},
  "network": {"bytes_recv": 3, "bytes_sent": 4},
  "listening_ports": [{"proto": "tcp", "port": 22, "address": "0.0.0.0"}]
}
```

### Batch (dashboard)

`GET /api/servers/metrics` → `{ "servers": [ { "id", "display_name", "hostname", "ssh_port", "auth_type", "metrics": {…} } ] }`

Schemas: `schemas/metrics.py`, `schemas/server.py` (`ServerPublicSchema`).

## UI refresh

Dashboard cards and the detail page auto-refresh about every **10 seconds**, with **Refresh now**. JS only calls the APIs above (`static/js/metrics.js`).

## Tests

Local paths mock `psutil`. Remote paths mock SSH (`connect_ssh`) — no real external SSH in CI.

```bash
pytest tests/test_metrics.py
```
